import abc
import param as pm

from proposal_inverter import Wallet, ProposalInverter


class WhitelistMechanism(pm.Parameterized):
    votes = pm.Dict(dict(), doc="maps broker public keys to a dictionary of the vote history")

    def __init__(self, **params):
        super().__init__(**params)

        self.whitelist = set()
        self.waitlist = set()

    @abc.abstractmethod
    def vote(self, proposal: ProposalInverter, voter: Wallet, broker: Wallet, vote: bool):
        if broker.public not in self.whitelist:
            self.waitlist(broker)
            self.votes[broker.public][voter.public] = vote

    def waitlist(self, broker: Wallet):
        if broker.public not in self.whitelist and broker.public not in self.waitlist.keys():
            self.votes[broker.public] = dict()

    def whitelist(self, broker: Wallet):
        self.whitelist.add(broker.public)

        if broker.public in self.waitlist.keys():
            del self.waitlist[broker.public]


class OwnerVoteOnly(WhitelistMechanism):
    def vote(self, proposal: ProposalInverter, voter: Wallet, broker: Wallet, vote: bool):
        super().vote(proposal, voter, broker, vote)

        if voter.public == proposal.owner_address and vote is True:
            self.whitelist(broker)


class PayerVote(WhitelistMechanism):
    def vote(self, proposal: ProposalInverter, voter: Wallet, broker: Wallet, vote: bool):
        super().vote(proposal, voter, broker, vote)

        if voter.public in proposal.payer_contributions.keys() and vote is True:
            self.whitelist(broker)


class EqualVote(WhitelistMechanism):
    min_vote = pm.Number(0.5, doc="the minimum percentage of votes needed to whitelist a broker")

    def vote(self, proposal: ProposalInverter, voter: Wallet, broker: Wallet, vote: bool):
        super().vote(proposal, voter, broker, vote)

        vote = sum([1 * vote in self.votes[broker.public].items()])
        n_payers = len(proposal.payer_contributions)

        if vote / n_payers >= self.min_vote:
            self.whitelist(broker)


class WeightedVote(WhitelistMechanism):
    min_vote = pm.Number(0.5, doc="the minimum percentage of weighted votes needed to whitelist a broker")

    def vote(self, proposal: ProposalInverter, voter: Wallet, broker: Wallet, vote: bool):
        super().vote(proposal, voter, broker, vote)

        weighted_vote = sum([
            proposal.payer_contributions[payer] * vote
            for payer, vote in self.votes[broker.public].items()
        ])
        total_contributions = sum(proposal.payer_contributions.values())

        if weighted_vote / total_contributions >= self.min_vote:
            self.whitelist(broker)


class ConsensusVote(WhitelistMechanism):
    def vote(self, proposal: ProposalInverter, voter: Wallet, broker: Wallet, vote: bool):
        super().vote(proposal, voter, broker, vote)

        consensus = all([
            self.votes[broker.public].get(payer, False)
            for payer in proposal.payer_contributions.keys()
        ])

        if consensus:
            self.whitelist(broker)
