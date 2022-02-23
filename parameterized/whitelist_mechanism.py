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

    def add_waitlist(self, broker: "Wallet") -> None:
        """
        Adds a broker to the waitlist if they are not already in the waitlist or
        whitelist.
        """
        self.waitlist.add(broker.public)

        if broker.public not in self.votes.keys():
            self.votes[broker.public] = dict()

    def in_waitlist(self, broker: "Wallet") -> bool:
        """
        Checks if the broker is currently in the waitlist.
        """
        return broker.public in self.waitlist

    def in_whitelist(self, broker: "Wallet") -> bool:
        """
        Checks if the broker is currently in the whitelist.
        """
        return broker.public in self.whitelist

    def vote(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet", vote: bool) -> None:
        """
        This method should be overrided in all child classes.

        `super().vote()` should be called in the overrided method when a vote is
        cast. The overrided method should also determine two cases:

        1.  The case where the minimum conditions are met, and the broker is 
            removed from the waitlist and added to the whitelist.
        2.  The case where the minimum conditions are no longer met, and the
            broker is removed from the whitelist and added back to the waitlist.
        """
        if self._vote_condition(proposal, voter, broker):
            if not self.in_whitelist(broker) and not self.in_waitlist(broker):
                self.add_waitlist(broker)

            self.votes[broker.public][voter.public] = vote

            if self._add_condition(proposal, voter, broker):
                self._add_whitelist(broker)
            elif self._remove_condition(proposal, voter, broker) and self.in_whitelist(broker):
                self._remove_whitelist(broker)

    @abstractmethod
    def _vote_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return True

    @abstractmethod
    def _add_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return True

    @abstractmethod 
    def _remove_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return True

    def _add_whitelist(self, broker: "Wallet") -> None:
        """
        Removes a broker from the waitlist and adds them to the whitelist.
        """
        self._remove_waitlist(broker)
        self.whitelist.add(broker.public)

    def _remove_waitlist(self, broker: "Wallet") -> None:
        """
        Removes a broker from the the waitlist.
        """
        self.waitlist.discard(broker.public)

    def _remove_whitelist(self, broker: "Wallet") -> None:
        """
        Removes broker from the whitelist and adds them to the waitlist.
        """
        self.whitelist.discard(broker.public)
        self.add_waitlist(broker)


class NoVote(WhitelistMechanism):
    """
    This is a permissionless whitelist mechanism. In this mechanism, votes are
    not counted, and all brokers are on the whitelist.
    """

    def in_waitlist(self, broker: "Wallet") -> bool:
        return False

    def in_whitelist(self, broker: "Wallet") -> bool:
        return True

    def vote(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet", vote: bool) -> None:
        pass

    def _vote_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return True

    def _add_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return True

    def _remove_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return True


class OwnerVote(WhitelistMechanism):
    """
    In this mechanism, the owner of the proposal has full control of which
    brokers get whitelisted. Any votes cast by anyone who is not the owner are
    not counted.
    """
    def _vote_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        voter_is_owner = voter.public == proposal.owner_address

        return voter_is_owner is True

    def _add_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        owner_vote_true = self.votes[broker.public][voter.public]

        return owner_vote_true is True

    def _remove_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        owner_vote_false = self.votes[broker.public][voter.public]

        return owner_vote_false is False


class PayerVote(WhitelistMechanism):
    """
    In this mechanism, any payer, including the owner, has control over which
    brokers get whitelisted. Only one payer is required to approve a broker for
    a broker to get whitelisted.
    """
    def _vote_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        voter_is_payer = voter.public in proposal.payer_agreements.keys()

        return voter_is_payer

    def _add_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        any_payer_vote_true = any(self.votes[broker.public].values())

        return any_payer_vote_true is True

    def _remove_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        all_payers_vote_false = all(self.votes[broker.public].values())

        return all_payers_vote_false is False


class EqualVote(WhitelistMechanism):
    """
    In this mechanism, each payer has equal voting power. The fraction of payers
    that approve a broker must pass a minimum threshold before the broker is
    whitelisted.
    """
    min_vote = pm.Number(0.5, doc="the minimum percentage of votes needed to whitelist a broker")

    def _vote_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        voter_is_payer = voter.public in proposal.payer_agreements.keys()

        return voter_is_payer

    def _add_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return self._voter_fraction(proposal, broker) >= self.min_vote

    def _remove_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return self._voter_fraction(proposal, broker) < self.min_vote

    def _voter_fraction(self, proposal: "ProposalInverter", broker: "Wallet") -> float:
        vote = sum([1 * vote for vote in self.votes[broker.public].values()])
        n_payers = len(proposal.payer_agreements)

        return vote / n_payers


class WeightedVote(WhitelistMechanism):
    """
    In this mechanism, each payer's vote is weighted by their total contribution
    of funds to the proposal. This means that voters who have contributed more
    have more voting power. The fraction of the weighted vote that approve a
    broker must pass a minimum threshold before the broker is whitelisted.
    """
    min_vote = pm.Number(0.5, doc="the minimum percentage of weighted votes needed to whitelist a broker")

    def _vote_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        voter_is_payer = voter.public in proposal.payer_agreements.keys()

        return voter_is_payer

    def _add_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return self._weighted_vote_fraction(proposal, broker) >= self.min_vote

    def _remove_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return self._weighted_vote_fraction(proposal, broker) < self.min_vote

    def _weighted_vote_fraction(self, proposal: "ProposalInverter", broker: "Wallet") -> float:
        weighted_vote = sum([
            proposal.payer_agreements[payer].total_contributions() * vote
            for payer, vote in self.votes[broker.public].items()
        ])
        total_contributions = sum(
            [agreement.total_contributions() for agreement in proposal.payer_agreements.values()]
        )
        print(weighted_vote, total_contributions)

        return weighted_vote / total_contributions


class UnanimousVote(WhitelistMechanism):
    """
    In this mechanism, every payer must approve a broker before they are
    whitelisted. The approval must be unanimous, meaning each payer has equal
    veto power.
    """
    def _vote_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        voter_is_payer = voter.public in proposal.payer_agreements.keys()

        return voter_is_payer

    def _add_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return self._unanimous(proposal, broker) is True

    def _remove_condition(self, proposal: "ProposalInverter", voter: "Wallet", broker: "Wallet") -> bool:
        return self._unanimous(proposal, broker) is False

    def _unanimous(self, proposal: "ProposalInverter", broker: "Wallet") -> bool:
        unanimous = all([
            self.votes[broker.public].get(payer, False)
            for payer in proposal.payer_agreements.keys()
        ])

        return unanimous
