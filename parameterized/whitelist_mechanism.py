import param as pm

from abc import abstractmethod


class WhitelistMechanism(pm.Parameterized):
    """
    This is the base class for all whitelisting mechanisms. Any new whitelisting
    mechanism should override the `vote()` method and call `super().vote()`
    depending on if the specified permissions are met.

    The whitelist mechanism has three stages:
    
      - A broker is added to the waitlist. This is where all brokers are stored
        until they are whitelisted. There is no blacklist so that voters can
        change their vote at a later time.
      - A voter votes for a broker. Depending on the mechanism, it may require
        more than a single vote for a broker to be whitelisted.
      - Once enough votes for a broker has been cast, the broker is removed from
        the waitlist and is added to the whitelist.
    """
    votes = pm.Dict(dict(), doc="maps broker public keys to a dictionary of the vote history")

    def __init__(self, **params):
        super().__init__(**params)

        self.whitelist = set()
        self.waitlist = set()

    @abstractmethod
    def vote(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet", vote: bool):
        """
        This method should be overrided in all child classes.

        `super().vote()` should be called in the overrided method when a vote is
        cast.
        """
        if broker.public not in self.whitelist:
            self.add_waitlist(broker)
            self.votes[broker.public][voter.public] = vote

    def add_waitlist(self, broker: "Wallet"):
        """
        Adds a broker to the waitlist if they are not already in the waitlist or
        whitelist.
        """
        if not self.in_whitelist(broker) and not self.in_waitlist(broker):
            self.waitlist.add(broker.public)
            self.votes[broker.public] = dict()

    def in_waitlist(self, broker: "Wallet"):
        """
        Checks if the broker is currently in the waitlist.
        """
        return broker.public in self.waitlist

    def add_whitelist(self, broker: "Wallet"):
        """
        Removes a broker from the waitlist and adds them to the whitelist.
        """
        self.waitlist.remove(broker.public)
        self.whitelist.add(broker.public)

    def in_whitelist(self, broker: "Wallet"):
        """
        Checks if the broker is currently in the whitelist.
        """
        return broker.public in self.whitelist


class NoVote(WhitelistMechanism):
    """
    This is a permissionless whitelist mechanism. In this mechanism, votes are
    not counted, and all brokers are on the whitelist.
    """
    def vote(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet", vote: bool):
        pass

    def in_waitlist(self, broker: "Wallet"):
        return False

    def in_whitelist(self, broker: "Wallet"):
        return True


class OwnerVote(WhitelistMechanism):
    """
    In this mechanism, the owner of the proposal has full control of which
    brokers get whitelisted. Any votes cast by anyone who is not the owner are
    not counted.
    """
    def vote(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet", vote: bool):
        if voter.public == proposal.owner_address:
            super().vote(proposal, voter, broker, vote)

            if vote is True:
                self.add_whitelist(broker)


class PayerVote(WhitelistMechanism):
    """
    In this mechanism, any payer, including the owner, has control over which
    brokers get whitelisted. Only one payer is required to approve a broker for
    a broker to get whitelisted.
    """
    def vote(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet", vote: bool):
        if voter.public == proposal.owner_address or voter.public in proposal.payer_contributions.keys():
            super().vote(proposal, voter, broker, vote)

            if vote is True:
                self.add_whitelist(broker)


class EqualVote(WhitelistMechanism):
    """
    In this mechanism, each payer has equal voting power. The fraction of payers
    that approve a broker must pass a minimum threshold before the broker is
    whitelisted.
    """
    min_vote = pm.Number(0.5, doc="the minimum percentage of votes needed to whitelist a broker")

    def vote(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet", vote: bool):
        if voter.public in proposal.payer_contributions.keys():
            super().vote(proposal, voter, broker, vote)

            vote = sum([1 * vote for vote in self.votes[broker.public].values()])
            n_payers = len(proposal.payer_contributions)

            if vote / n_payers >= self.min_vote:
                self.add_whitelist(broker)


class WeightedVote(WhitelistMechanism):
    """
    In this mechanism, each payer's vote is weighted by their total contribution
    of funds to the proposal. This means that voters who have contributed more
    have more voting power. The fraction of the weighted vote that approve a
    broker must pass a minimum threshold before the broker is whitelisted.
    """
    min_vote = pm.Number(0.5, doc="the minimum percentage of weighted votes needed to whitelist a broker")

    def vote(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet", vote: bool):
        if voter.public in proposal.payer_contributions.keys():
            super().vote(proposal, voter, broker, vote)

            weighted_vote = sum([
                proposal.payer_contributions[payer] * vote
                for payer, vote in self.votes[broker.public].items()
            ])
            total_contributions = sum(proposal.payer_contributions.values())

            if weighted_vote / total_contributions >= self.min_vote:
                self.add_whitelist(broker)


class UnanimousVote(WhitelistMechanism):
    """
    In this mechanism, every payer must approve a broker before they are
    whitelisted. The approval must be unanimous, meaning each payer has equal
    veto power.
    """
    def vote(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet", vote: bool):
        if voter.public in proposal.payer_contributions.keys():
            super().vote(proposal, voter, broker, vote)

            unanimous = all([
                self.votes[broker.public].get(payer, False)
                for payer in proposal.payer_contributions.keys()
            ])

            if unanimous:
                self.add_whitelist(broker)
