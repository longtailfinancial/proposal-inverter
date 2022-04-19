import pytest

from parameterized.proposal_inverter import Wallet, ProposalInverter
from parameterized.whitelist_mechanism import NoVote, OwnerVote


@pytest.fixture
def owner():
    owner = Wallet({"USD": 1000})

    return owner


@pytest.fixture
def inverter(owner):
    inverter = owner.deploy({"USD": 500}, broker_whitelist=NoVote())

    return inverter


@pytest.fixture
def broker1():
    broker1 = Wallet({"USD": 100})

    return broker1


@pytest.fixture
def broker2():
    broker2 = Wallet({"USD": 100})

    return broker2


@pytest.fixture
def payer():
    payer = Wallet({"USD": 100})

    return payer


def test_claim(inverter, broker1, broker2):
    """
    Test that the brokers receive the correct amounts of funds when they claim
    their funds before the minimum number of epochs. When they make a claim
    after the minimum number of epochs, they should also receive their stake.
    """
    # Add broker to proposal inverter
    broker1 = inverter.join(broker1, {"USD": 50})

    # Make a claim before the minimum number of epochs
    inverter.iter_epoch(10)

    broker1 = inverter.claim(broker1)

    assert inverter.funds == {"USD": 400}
    assert inverter.stake == {"USD": 50}
    assert broker1.funds == {"USD": 150}

    # Add a second broker
    broker2 = inverter.join(broker2, {"USD": 50})

    # Make a claim before the minimum number of epochs
    inverter.iter_epoch(10)

    broker2 = inverter.claim(broker2)

    assert inverter.funds == {"USD": 350}
    assert inverter.stake == {"USD": 100}
    assert broker2.funds == {"USD": 100}

    # Make a claim after the minimum number of epochs
    inverter.iter_epoch(10)

    broker1 = inverter.claim(broker1)

    assert inverter.funds == {"USD": 250}
    assert inverter.stake == {"USD": 100}
    assert broker1.funds == {"USD": 250}


def test_join(inverter, broker1):
    """ "
    Simple test to add a single broker and check the properties of the proposal
    inverter.
    """
    broker1 = inverter.join(broker1, {"USD": 50})

    assert inverter.funds == {"USD": 500}
    assert inverter.stake == {"USD": 50}
    assert inverter.get_number_of_brokers() == 1

    assert broker1.funds == {"USD": 50}


def test_leave(inverter, broker1, broker2):
    """
    Ensure that when a broker leaves the proposal inverter, they receive their
    stake if they have stayed for the minimum number of epochs.
    """
    # Add brokers
    broker1 = inverter.join(broker1, {"USD": 100})
    broker2 = inverter.join(broker2, {"USD": 100})

    assert inverter.get_number_of_brokers() == 2
    assert inverter.funds == {"USD": 500}
    assert inverter.stake == {"USD": 200}

    inverter.iter_epoch(20)

    # Remove a broker before the minimum number of epochs
    broker1 = inverter.leave(broker1)

    assert inverter.get_number_of_brokers() == 1
    assert inverter.funds == {"USD": 500}
    assert inverter.stake == {"USD": 100}
    assert broker1.funds == {"USD": 100}

    # Remove a broker while over the minimum number of epochs
    inverter.iter_epoch(10)

    broker2 = inverter.leave(broker2)

    assert inverter.get_number_of_brokers() == 0
    assert inverter.funds == {"USD": 300}
    assert broker2.funds == {"USD": 300}


def test_pay(inverter, payer):
    """
    Payer contributes more than minimum contribution and is accepted.
    """
    payer = inverter.pay(payer, {"USD": 25})

    assert payer.funds == {"USD": 75}
    assert inverter.funds == {"USD": 525}


def test_pay_lower_than_minimum(inverter, payer):
    """
    Payer cannot contribute lower than minimum contribution
    """
    payer = inverter.pay(payer, {"USD": 1})

    assert payer.funds == {"USD": 100}
    assert inverter.funds == {"USD": 500}


def test_get_allocated_funds(inverter, broker1, broker2):
    assert inverter.get_allocated_funds() == {}

    # Add broker
    broker1 = inverter.join(broker1, {"USD": 100})

    # Add a second broker
    inverter.iter_epoch(10)

    broker2 = inverter.join(broker2, {"USD": 100})

    assert inverter.funds == {"USD": 500}
    assert inverter.stake == {"USD": 200}
    assert inverter.get_number_of_brokers() == 2
    assert inverter.get_allocated_funds() == {"USD": 100}

    inverter.iter_epoch(20)

    assert inverter.get_allocated_funds() == {"USD": 300}


def test_cancel(owner, inverter, broker1, broker2):
    # Add brokers (each with a different initial stake)
    broker1 = inverter.join(broker1, {"USD": 50})
    broker2 = inverter.join(broker2, {"USD": 100})

    # Check total funds: 500(owner initial amount), 150 from stakes
    assert inverter.funds == {"USD": 500}
    assert inverter.stake == {"USD": 150}

    inverter.iter_epoch(30)

    # Cancel the proposal inverter
    inverter.cancel(owner.public)

    # Each broker leaves the proposal
    broker1 = inverter.leave(broker1)
    broker2 = inverter.leave(broker2)

    # Broker1 funds = 50 (current funds) + 50 (stake) + 150 (claim) + 70/2 = 285
    # 70/2 = (allocation_per_epoch * min_horizon)/ num_of_brokers
    assert broker1.funds == {"USD": 285}

    # Broker2 funds = 0 (current funds) + 100 (stake) + 150 (claim) + 70/2 = 285
    # 70/2 = (allocation_per_epoch * min_horizon)/ num_of_brokers
    assert broker2.funds == {"USD": 285}

    # Owner funds = 500 (current funds) + (500 - 300 - 70) = 630
    # 300 = funds allocated to brokers
    # 70 = minimum horizon allocated to brokers
    owner = inverter.claim(owner)

    # End state of proposal inverter
    assert owner.funds == {"USD": 630}
    assert inverter.funds == {"USD": 0}


def test_forced_cancel(broker1):
    """
    Cancellation occurs when the inverter is below the minimum horizon and all brokers leave. In this case, there
    are no brokers to allocate the funds to, so when the forced cancel is triggered, all funds should be returned to the
    owner.
    """
    # Deploy proposal inverter
    owner = Wallet(funds={"USD": 1000})
    inverter = owner.deploy({"USD": 100}, broker_whitelist=NoVote())

    # Add broker
    broker1 = inverter.join(broker1, {"USD": 9})

    # Dip below the minimum conditions
    inverter.iter_epoch(5)

    broker1 = inverter.leave(broker1)

    assert inverter.get_number_of_brokers() == 0
    assert inverter.get_horizon() < inverter.min_horizon
    assert inverter.get_allocated_funds() == inverter.funds


def test_owner_whitelist(owner, broker1, payer):
    inverter = owner.deploy({"USD": 500}, broker_whitelist=OwnerVote())

    # Broker applies to proposal, but not yet whitelisted
    broker1 = inverter.join(broker1, {"USD": 10})

    assert broker1.funds == {"USD": 100}
    assert inverter.get_number_of_brokers() == 0

    # Owner adds broker to whitelist
    inverter.vote_broker(owner, broker1, True)
    broker1 = inverter.join(broker1, {"USD": 10})

    assert broker1.funds == {"USD": 90}
    assert inverter.get_number_of_brokers() == 1

    # Owner removes broker from whitelist
    inverter.vote_broker(owner, broker1, False)
    broker1 = inverter.leave(broker1)

    assert broker1.funds == {"USD": 90}
    assert inverter.get_number_of_brokers() == 0

    # Broker tries to apply to proposal again after being removed from whitelist
    broker1 = inverter.join(broker1, {"USD": 10})

    assert broker1.funds == {"USD": 90}
    assert inverter.get_number_of_brokers() == 0
