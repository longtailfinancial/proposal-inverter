import param as pm

from collections import defaultdict

from funds import Funds


class WalletAgreement(pm.Parameterized):
    """Stores data about a wallet in the proposal inverter.

    In the base class, the data points that are relevant to both brokers and
    payers are specified.
    """
    allocated_funds = pm.ClassSelector(Funds, default=Funds(), doc="total funds that a wallet has yet to claim")
    claimed_funds = pm.ClassSelector(Funds, default=Funds(), doc="total funds that a wallet has claimed thus far")

    def total_allocated(self):
        return self.allocated_funds.total_funds()

    def total_claimed(self):
        return self.total_claimed.total_funds()


class BrokerAgreement(WalletAgreement):
    """
    Stores data about a broker in the proposal inverter.
    """
    epoch_joined = pm.Number(0, constant=True, doc="epoch at which this broker joined")
    stake = pm.ClassSelector(Funds, default=Funds(), doc="total funds staked")

    def total_staked(self):
        return self.stake.total_funds()
    
    
class PayerAgreement(WalletAgreement):
    """
    Stores data about a payer in the proposal inverter.
    """
    contributions = pm.Dict(defaultdict(Funds), doc="maps the epoch number to the amount of funds a payer contributed during that epoch")

    def total_contributions(self):
        return sum([
            contribution.total_funds() 
            for contribution in self.contributions.values()
        ])
