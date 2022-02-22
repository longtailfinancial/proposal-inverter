from parameterized.funds import Funds
from parameterized.proposal_inverter import Wallet
from parameterized.whitelist_mechanism import NoVote


def test_deploy():
    owner = Wallet(funds={"USD": 1000})
    inverter = owner.deploy(funds={"USD": 500}, broker_whitelist=NoVote())

    assert inverter.funds == {"USD": 500}
    assert inverter.current_epoch == 0
    assert inverter.number_of_brokers() == 0
