import numpy as np
import param as pm
import pandas as pd
import panel as pn
import secrets

from collections import defaultdict
from eth_account import Account

from parameterized.agreement import BrokerAgreement, PayerAgreement
from parameterized.funds import Funds
from parameterized.whitelist_mechanism import WhitelistMechanism, NoVote, OwnerVote, PayerVote, EqualVote, WeightedVote, UnanimousVote


pn.extension()


def generate_eth_account():
    priv = secrets.token_hex(32)
    private = "0x" + priv
    public = Account.from_key(private).address

    return private, public


class Wallet(pm.Parameterized):
    """
    number_of_features represents the number of features that a wallet accounts for when reviewing a proposal, 
    which is represented by wallet types. The wallet types for this example are which in this example are 
    (T1: Loyal, T2: Frugal, T3: Time sensitive, T4: Greedy, F5: Philanthropic). For further details into 
    what each Wallet type represents, refer to the Proposal Inverter: Matrix factorization Hackmd. Please
    note: number of wallets must be equal to the number of proposal features.
    """
    funds = pm.ClassSelector(Funds, default=Funds(), doc="stores the funds in this wallet")

    feature_vector = pm.ClassSelector(np.ndarray, doc="stores each wallet's characteristics as features in a vector")
    number_of_features = pm.Number(5, constant=True, doc="number of wallet features")
    
    def __init__(self, funds: dict|Funds = dict(), **params):
        super().__init__(**params)

        self.funds = Funds(funds)

        self.private, self.public = generate_eth_account()

        self.joined = set()
        self.paid = set()
        self.owned = set()
 
    def deploy(self, funds: dict|Funds, **params):
        """
        An actor within the ecosystem can deploy a new agreement contract by specifying which proposal the agreement 
        supports, setting the parameters of the smart contract providing initial funds, and providing any (unenforced) 
        commitment to continue topping up the contract as payer under as long as a set of SLAs are met. For the purpose 
        of this draft, it is assumed that the contract is initialized with some quantity of funds F such that H>Hmin 
        and that B=∅.
        """
        if self.funds < funds:
            print("Wallet does not have sufficient funds to deploy a proposal")

            return None

        self.funds -= funds

        proposal = ProposalInverter(owner=self, funds=funds, **params)

        self.owned.add(proposal.public)

        return proposal


class ProposalInverter(Wallet):
    """
    number_of_features represents the number of features that are present in a proposal, which in 
    this example are (F1: Location, F2: Simplicity, F3:Profitability, F4: Low time commitment, 
    F5: Environmental/Humanitarian proposal). For further details into what each factor represents, 
    refer to Proposal Inverter: Matrix factorization Hackmd. Please note: number of features must be 
    equal for both wallets and proposals.
    """
    # State
    cancelled = pm.Boolean(False, doc="if the proposal has been cancelled, funds will no longer be allocated")
    current_epoch = pm.Number(0, doc="number of epochs that have passed")
    stake = pm.ClassSelector(Funds, default=Funds(), doc="The total broker stake")

    broker_agreements = pm.Dict(dict(), doc="maps each broker's public key to their broker agreement")
    payer_agreements = pm.Dict(dict(), doc="maps each payer's public key to their Payer agreement")

    broker_whitelist = pm.ClassSelector(WhitelistMechanism, default=OwnerVote())
    payer_whitelist = pm.ClassSelector(WhitelistMechanism, default=NoVote())
    
    # Parameters
    allocation_per_epoch = pm.Number(10, doc="funds allocated to all brokers per epoch in USD")
    epoch_length = pm.Number(60*60*24, doc="length of one epoch, measured in seconds")
    max_brokers = pm.Number(5, doc="maximum number of brokers that can join")
    min_contribution = pm.Number(5, doc="minimum funds that a payer must contribute to join")
    min_epochs = pm.Number(28, doc="minimum number of epochs that must pass for a broker to exit and take their stake")
    min_horizon = pm.Number(7, doc="minimum number of future epochs the proposal inverter can allocate funds for")
    min_payers = pm.Number(1, doc="minimum number of payers that need to commit before any funds are released")
    min_brokers = pm.Number(1, doc="minimum number of brokers required to continue")
    min_stake = pm.Number(5, doc="minimum funds that a broker must stake to join in USD")
    
    def __init__(self, owner: Wallet, **params):
        super().__init__(**params)

        self.owner_address = owner.public

        # Manually add owner to whitelist and track owner contribution
        self.payer_whitelist.whitelist.add(owner.public)
        self.payer_agreements[owner.public] = PayerAgreement()
        self.payer_agreements[owner.public].contributions[self.current_epoch] += self.funds

        self.started = self.__minimum_conditions_met()

        if not self.started:
            print("ProposalInverter :: proposal deployed without meeting minimum conditions")
    
    def cancel(self, owner_address):
        """
        In the event that the owner closes down a contract, each Broker gets back their stake, and recieves any 
        unclaimed tokens allocated to their address as well an equal share of the remaining unallocated assets.
        
        That is to say the quantity Δdi of data tokens is distributed to each broker i∈B
        Δdi=si+ai+RN
        and thus the penultimate financial state of the contract is
        S=0R=0A=0
        when the contract is self-destructed.
        """
        if owner_address != self.owner_address:
            print("Only the owner can cancel a proposal")
        elif self.cancelled:
            print("Proposal has already been cancelled")
        else:
            allocated_funds = self.get_allocated_funds()       
            allocation = self.get_allocation()

            # This is equivalent to `allocation_per_epoch * min_horizon` except
            # it factors into account the case where the total funds is lower
            # than the minimum horizon
            horizon_funds = Funds()
            for epoch in range(self.min_horizon):
                horizon_funds += min(allocation, self.funds - allocated_funds - horizon_funds)

            for public_key, agreement in self.broker_agreements.items():
                agreement.allocated_funds += horizon_funds / self.get_number_of_brokers()

            for public_key, agreement in self.payer_agreements.items():
                # The funder returns are based on the amount that funder contributed
                funder_funds = agreement.total_contributions()
                agreement.allocated_funds += (self.funds - allocated_funds - horizon_funds) * (funder_funds / self.funds.total_funds())

            self.cancelled = True

    def claim(self, wallet: Wallet):
        """
        Since claiming funds works the same way for brokers and payers, the
        funds allocated to that wallet are added.
        """
        wallet = self.__claim_broker_funds(wallet)
        wallet = self.__claim_payer_funds(wallet)

        return wallet

    def join(self, broker: Wallet, stake: dict|Funds):
        """
        A broker can join the agreement (and must also join the stream associated with that agreement) by staking the
        minimum stake.
        
        Note that if the act of joining would cause |B+|>nmax then joining would fail. It is not possible for more than
        `n_max` brokers to be party to this agreement.
        Furthermore, it is possible to enforce addition access control via whitelists or blacklists which serve to
        restrict access to the set of brokers. These lists may be managed by the owner, the payers, and/or the brokers;
        however, scoping an addition access control scheme is out of scope at this time.
        """
        stake = Funds(stake)

        if broker.funds < stake:
            raise ValueError("Failed to add broker due to insufficient funds")
        elif broker.public in self.broker_agreements.keys():
            print("Failed to add broker, broker already has a stake in this proposal")
        elif self.get_number_of_brokers() + 1 > self.max_brokers:
            print("Failed to add broker, maximum number of brokers reached")
        elif stake.total_funds() < self.min_stake:
            print("Failed to add broker, minimum stake not met")
        elif self.cancelled:
            print("Failed to add broker, proposal has been cancelled")
        elif self.broker_whitelist.in_whitelist(broker):
            broker.funds -= stake
            self.stake += stake

            self.broker_agreements[broker.public] = BrokerAgreement(
                epoch_joined=self.current_epoch,
                stake=stake,
            )

            broker.joined.add(self.public)
        else:
            self.broker_whitelist.add_waitlist(broker)
            print("Warning: broker not yet whitelisted, added to waitlist")

        return broker

    def leave(self, broker: Wallet):
        """
        In the event that the horizon is below the threshold or a broker has been attached to the agreement for more than
        the minimum epochs, a broker may exit an agreement and take their stake (and outstanding claims).
        However if a broker has not stayed for the entire period, or the contract is not running low on funds, the stake
        will be kept as payment by the agreement contract when the broker leaves.
        In a more extreme case we may require the broker to relinquish the claim as well but this would easily be skirted
        by making a claim action before leaving.
        """
        broker_agreement = self.broker_agreements.get(broker.public)

        if broker_agreement is None:
            print("Broker is not part of this proposal")
        else:
            if self.cancelled or self.current_epoch - broker_agreement.epoch_joined >= self.min_epochs:
                stake = broker_agreement.stake
                broker.funds += stake
                self.stake -= stake
            else:
                stake = broker_agreement.stake
                self.funds += stake
                self.stake -= stake

            broker = self.claim(broker)
            broker.joined.discard(self.public)
            del self.broker_agreements[broker.public]

        return broker

    def pay(self, payer: Wallet, tokens: dict|Funds):
        """
        A payer takes the action pay by providing a quantity of tokens (split into Stablecoins and DAO tokens) 
        ΔF, which increased the unallocated funds (and thus also the total funds).
        F+ = F + ΔF
        R+ = R + ΔF
        Furthermore, the Horizon H is increased 
        H+ = (R + ΔF)/ ΔA = H + (ΔF/ΔA)
        """
        tokens = Funds(tokens)

        if payer.funds < tokens:
            print("Payer does not have sufficient funds")
        elif tokens.total_funds() < self.min_contribution:
            print("Payer contribution is lower than minimum contribution")
        elif self.cancelled:
            print("Proposal has been cancelled, cannot add funds")
        elif self.payer_whitelist.in_whitelist(payer):

            if payer.public not in self.payer_agreements.keys():
                self.payer_agreements[payer.public] = PayerAgreement()
                payer.paid.add(self.public)

            self.payer_agreements[payer.public].contributions[self.current_epoch] += tokens

            payer.funds -= tokens
            self.funds += tokens
        else:
            self.payer_whitelist.add_waitlist(payer)
            print("Payer not yet whitelisted, added to waitlist")

        return payer
   
    def vote_broker(self, voter: Wallet, broker: Wallet, vote: bool):
        """
        This is the outward facing interface to directly affect which brokers
        are whitelisted. The actual mechanism is dependent on which whitelisting
        mechanism is used.
        """
        self.broker_whitelist.vote(self, voter, broker, vote)

    def vote_payer(self, voter: Wallet, payer: Wallet, vote: bool):
        """
        This is the outward facing interface to directly affect which payers are
        whitelisted. The actual mechanism is dependent on which whitelisting
        mechanism is used.
        """
        self.payer_whitelist.vote(self, voter, payer, vote)

    def iter_epoch(self, n_epochs: int=1):
        """
        Iterates to the next epoch and updates the total claimable funds for each broker.
        There may conditions under which any address may trigger the cancel but these conditions should be 
        indicative of a failure on the part of the payer. An example policy would be to allow forced cancel 
        when n < nmin and H < H min, and possibly only if this is the case more multiple epochs.
        """
        for epoch in range(n_epochs):
            if not self.cancelled:
                if not self.started:
                    self.started = self.__minimum_conditions_met()

                if self.started:
                    if not self.__minimum_conditions_met():
                        self.cancel(self.owner_address)
                    else:
                        self.__allocate_funds()

            self.current_epoch += 1
   
    def get_allocation(self):
        """
        Returns the allocated tokens for the current epoch. This is for the
        entire group of brokers, not per individual broker.
        """
        unallocated_funds = self.funds - self.get_allocated_funds()
        total_unallocated_funds = self.funds.total_funds() - self.get_total_allocated_funds()

        return self.allocation_per_epoch * unallocated_funds / total_unallocated_funds
 
    def get_allocated_funds(self):
        """
        Returns the total unclaimed allocated funds in their native tokens.
        """
        broker_allocated = sum([agreement.allocated_funds for agreement in self.broker_agreements.values()], start=Funds())
        payer_allocated = sum([agreement.allocated_funds for agreement in self.payer_agreements.values()], start=Funds())

        return broker_allocated + payer_allocated

    def get_horizon(self):
        """
        Returns the current horizon.
        """
        return (self.funds.total_funds() - self.get_total_allocated_funds()) / self.allocation_per_epoch
 
    def get_number_of_brokers(self):
        return len(self.broker_agreements.keys())
 
    def get_total_allocated_funds(self):
        """
        Returns the total unclaimed allocated funds from all broker and payer
        agreements converted into USD.
        """
        broker_allocated = sum([agreement.total_allocated() for agreement in self.broker_agreements.values()])
        payer_allocated = sum([agreement.total_allocated() for agreement in self.payer_agreements.values()])

        return broker_allocated + payer_allocated

    def __allocate_funds(self):
        """
        Allocates funds for one epoch to all the brokers.
        """
        allocation_per_broker = self.get_allocation() / self.get_number_of_brokers()

        for agreement in self.broker_agreements.values():
            agreement.allocated_funds += allocation_per_broker


    def __claim_broker_funds(self, broker: Wallet):
        """
        A broker that is attached to an agreement can claim their accumulated rewards at their discretion.
        Note that while this decreases the total funds in the contract it does not decrease the unallocated (remaining)
        funds in the conract because claims only extract claims according to a deterministic rule computed over the past.
        Many brokers may choose to claim their funds more or less often depending on opportunity costs and gas costs.
        Preferred implementations may vary – see section on synthetics state.
        """
        broker_agreement = self.broker_agreements.get(broker.public)

        if broker_agreement is None:
            print("Broker is not part of this proposal, no funds are claimed")
        else:
            claim = broker_agreement.allocated_funds

            for token, n_tokens in claim.items():
                broker_agreement.allocated_funds[token] = 0
                broker_agreement.claimed_funds[token] += n_tokens
                broker.funds[token] += n_tokens
                self.funds[token] -= n_tokens

        return broker

    def __claim_payer_funds(self, payer: Wallet):
        """
        When a proposal is cancelled, any excess funds that are not distributed
        to the brokers are returned to the payers as claimable funds.
        """
        payer_agreement = self.payer_agreements.get(payer.public)
        
        if payer_agreement is None:
            print("Payer is not part of this proposal")
        else:
            claim = payer_agreement.allocated_funds

            payer_agreement.allocated_funds = Funds()
            payer_agreement.claimed_funds += claim
            payer.funds += claim
            self.funds -= claim

        return payer

    def __minimum_conditions_met(self):
        """
        Checks if the proposal currently meets the minimum conditions. The
        minimum start conditions are currently:
        - If the specified minimum number of payers has been met
        - If the specified minimum horizon has been met
        """
        min_brokers_met = self.get_number_of_brokers() >= self.min_brokers
        min_payers_met = len(self.payer_agreements.keys()) >= self.min_payers
        min_horizon_met = self.get_horizon() >= self.min_horizon

        return min_brokers_met and min_payers_met and min_horizon_met
