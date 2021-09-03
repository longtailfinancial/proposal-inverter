import param as pm
import panel as pn
from eth_account import Account
import secrets
pn.extension()


def generate_eth_account():
    priv = secrets.token_hex(32)
    private = "0x" + priv
    public = Account.from_key(private).address
    return (private, public)

class Wallet(pm.Parameterized):
    funds = pm.Number(100)
    def __init__(self, **params):
        super(Wallet, self).__init__(**params)
        (private, public) = generate_eth_account()
        self.private = private
        self.public = public
        
        
class Broker(Wallet):
    pass


class ProposalInverter(Wallet):
    # State
    
    # Parameters
    required_stake = pm.Number(5)
    epoch_length = pm.Number(60*60*24)
    min_epochs = pm.Number(28)
    allocation_per_epoch = pm.Number(10)
    min_horizon = pm.Number(7)
    min_brokers = pm.Number(1)
    max_brokers = pm.Number(5)
    committed_brokers = set()
    broker_claimable_funds = dict()
    owner = str()
    
    def __init__(self, owner: Wallet, initial_funds: float, **params):
        super(ProposalInverter, self).__init__(**params)
        self.owner_address = owner.public
        if owner.funds >= initial_funds:
            owner.funds -= initial_funds
            self.total_funds = initial_funds
    
    def add_broker(self, b: Broker):
        self.committed_brokers.add(b)
        
    def remove_broker(self, b: Broker):
        self.committed_brokers.remove(b)
        
    def number_of_brokers(self):
        return len(self.committed_brokers)
    
    def get_broker_claimable_funds(self):
        return self.allocation_per_epoch / self.number_of_brokers()
    
    
    def get_allocated_funds(self):
        pass
    
    def cancel(self):
        """
        In the event that the owner closes down a contract, each Broker gets back their stake, and recieves any 
        unclaimed tokens allocated to their address as well an equal share of the remaining unallocated assets.
        
        That is to say the quantity Δdi of data tokens is distributed to each broker i∈B

        Δdi=si+ai+RN

        and thus the penultimate financial state of the contract is

        S=0R=0A=0

        when the contract is self-destructed.
        """    
        pass
    
    
    
class Owner(Wallet):
    
    def _default_agreement_contract_params(self):
        params = dict(
            required_stake = 5,
            epoch_length = 60*60*24,
            min_epochs = 28,
            allocation_per_epoch = 10,
            min_horizon = 7,
            min_brokers = 1,
            max_brokers = 5,
        )
        return params
    
    def deploy(self, initial_funds, agreement_contract_params={}):
        """
        An actor within the ecosystem can deploy a new agreement contract by specifying which proposal the agreement 
        supports, setting the parameters of the smart contract providing initial funds, and providing any (unenforced) 
        commitment to continue topping up the contract as payer under as long as a set of SLAs are met. For the purpose 
        of this draft, it is assumed that the contract is initialized with some quantity of funds F such that H>Hmin 
        and that B=∅.
        """
        
        agreement_contract = ProposalInverter(
            owner = self,
            initial_funds = initial_funds,
            **agreement_contract_params,
        )
        
        return agreement_contract
        
    def cancel(self, agreement_contract):
        """
        In the event that the owner closes down a contract, each Broker gets back their stake, and recieves any 
        unclaimed tokens allocated to their address as well an equal share of the remaining unallocated assets.
        
        That is to say the quantity Δdi of data tokens is distributed to each broker i∈B

        Δdi=si+ai+RN

        and thus the penultimate financial state of the contract is

        S=0R=0A=0

        when the contract is self-destructed.
        """
        
        agreement_contract.cancel(self)