import param as pm

from collections import defaultdict


class WalletAgreement(pm.Parameterized):
    """Stores data about a wallet in the proposal inverter.

    In the base class, the data points that are relevant to both brokers and
    payers are specified.
    """
    allocated_funds = pm.Number(0, doc="total funds that the wallet can currently claim")
    total_claimed = pm.Number(0, doc="total funds the wallet has claimed thus far")


class BrokerAgreement(WalletAgreement):
    """
    Stores data about a broker in the proposal inverter.
    """
    epoch_joined = pm.Number(0, constant=True, doc="epoch at which this broker joined")
    initial_stake = pm.Number(0, constant=True, doc="total funds staked")
    
    
class PayerAgreement(WalletAgreement):
    """
    Stores data about a payer in the proposal inverter.
    """
    contributions = pm.Dict(defaultdict(int), doc="maps the epoch number to the amount of funds a payer contributed during that epoch")

    @property
    def total_contributions(self):
        return sum(self.contributions.values())
