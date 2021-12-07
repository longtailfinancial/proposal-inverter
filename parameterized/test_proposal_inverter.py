import pytest

from .proposal_inverter import Wallet, ProposalInverter
from .whitelist_mechanism import NoVote, OwnerVote


@pytest.fixture
def owner():
    owner = Wallet()
    owner.funds = 1000

    return owner


@pytest.fixture
def inverter(owner):
    inverter = owner.deploy(500, broker_whitelist=NoVote())

    return inverter


@pytest.fixture
def broker1():
    broker1 = Wallet()
    broker1.funds = 100

    return broker1


@pytest.fixture
def broker2():
    broker2 = Wallet()
    broker2.funds = 100

    return broker2


@pytest.fixture
def payer():
    payer = Wallet()
    payer.funds = 100

    return payer
    
    
def test_add_broker(inverter, broker1):
    """"
    Simple test to add a single broker and check the properties of the proposal inverter.
    """
    # Add broker to proposal inverter
    broker1 = inverter.add_broker(broker1, 50)

    assert inverter.funds == 500
    assert inverter.stake == 50
    assert inverter.number_of_brokers() == 1

    assert broker1.funds == 50


def test_claim_broker_funds(inverter, broker1, broker2):
    """
    Test that the brokers receive the correct amounts of funds when they claim their funds before the minimum number of
    epochs.
    """
    # Add broker to proposal inverter
    broker1 = inverter.add_broker(broker1, 50)

    # Make a claim before the minimum number of epochs
    inverter.iter_epoch(10)

    broker1 = inverter.claim_broker_funds(broker1)

    assert inverter.funds == 400
    assert inverter.stake == 50
    assert broker1.funds == 150

    # Add a second broker
    broker2 = inverter.add_broker(broker2, 50)

    # Make a claim before the minimum number of epochs
    inverter.iter_epoch(10)

    broker2 = inverter.claim_broker_funds(broker2)

    assert inverter.funds == 350
    assert inverter.stake == 100
    assert broker2.funds == 100

    # Make a claim after the minimum number of epochs
    inverter.iter_epoch(10)

    broker1 = inverter.claim_broker_funds(broker1)

    assert inverter.funds == 250
    assert inverter.stake == 100
    assert broker1.funds == 250

    
def test_remove_broker(inverter, broker1, broker2):
    """
    Ensure that when a broker leaves the proposal inverter, they receive their stake if they have stayed for the minimum
    number of epochs.
    """
    # Add brokers
    broker1 = inverter.add_broker(broker1, 100)
    broker2 = inverter.add_broker(broker2, 100)

    assert inverter.number_of_brokers() == 2
    assert inverter.funds == 500
    assert inverter.stake == 200

    inverter.iter_epoch(20)

    # Remove a broker before the minimum number of epochs
    broker1 = inverter.remove_broker(broker1)

    assert inverter.number_of_brokers() == 1
    assert inverter.funds == 500
    assert inverter.stake == 100
    assert broker1.funds == 100

    # Remove a broker while over the minimum number of epochs
    inverter.iter_epoch(10)

    broker2 = inverter.remove_broker(broker2)

    assert inverter.number_of_brokers() == 0
    assert inverter.funds == 300
    assert broker2.funds == 300

    
def test_get_allocated_funds(inverter, broker1, broker2):
    assert inverter.get_allocated_funds() == 0

    # Add broker
    broker1 = inverter.add_broker(broker1, 100)

    # Add a second broker
    inverter.iter_epoch(10)

    broker2 = inverter.add_broker(broker2, 100)

    assert inverter.funds == 500
    assert inverter.stake == 200
    assert inverter.number_of_brokers() == 2
    assert inverter.get_allocated_funds() == 100

    inverter.iter_epoch(20)

    assert inverter.get_allocated_funds() == 300


def test_pay(inverter, payer):
    # Payer contributes more than minimum contribution and is accepted
    payer = inverter.pay(payer, 25)

    assert payer.funds == 75
    assert inverter.funds == 525


def test_pay_lower_than_minimum(inverter, payer):
    # Payer cannot contribute lower than minimum contribution
    payer = inverter.pay(payer, 1)

    assert payer.funds == 100
    assert inverter.funds == 500

    
def test_cancel(owner, inverter, broker1, broker2):
    # Add brokers (each with a different initial stake)
    broker1 = inverter.add_broker(broker1, 50)
    broker2 = inverter.add_broker(broker2, 100)
    
    # Check total funds: 500(owner initial amount), 150 from stakes
    assert inverter.funds == 500
    assert inverter.stake == 150
    
    inverter.iter_epoch(30)
    
    # Cancel the proposal inverter
    inverter.cancel(owner.public)

    # Each broker leaves the proposal
    broker1 = inverter.remove_broker(broker1)
    broker2 = inverter.remove_broker(broker2)
        
    # Broker1 funds = 50 (current funds) + 50 (stake) + 250 (claim) = 350
    assert broker1.funds == 350
    
    # Broker2 funds = 0 (current funds) + 100 (stake) + 250 (claim) = 350
    assert broker2.funds == 350

    # End state of proposal inverter
    assert inverter.funds == 0
    assert inverter.get_allocated_funds() == 0


def test_forced_cancel_case1(broker1):
    """
    First test case occurs when the inverter is below the minimum horizon and all brokers leave. In this case, there
    are no brokers to allocate the funds to, so when the forced cancel is triggered, all funds should be returned to the
    owner.
    """
    # Deploy proposal inverter
    owner = Wallet()
    owner.funds = 1000
    inverter = owner.deploy(100, broker_whitelist=NoVote())
    
    # Add broker
    broker1 = inverter.add_broker(broker1, 9)
    
    # Dip below the minimum conditions
    inverter.iter_epoch(5)

    broker1 = inverter.remove_broker(broker1)
    print(inverter.broker_agreements)

    # Iterate past the buffer period
    inverter.iter_epoch(6)

    print(inverter.broker_agreements)

    assert inverter.number_of_brokers() == 1
    assert inverter.get_horizon() < inverter.min_horizon
    assert inverter.get_allocated_funds() == inverter.funds


def test_forced_cancel_case2(broker1, broker2, payer):
    """
    Second test case is to ensure the forced cancel counter resets if the inverter is no longer under the minimum
    conditions. The inverter dips below the minimum conditions for a few epochs less than the specified buffer period,
    and the goes back up. The counter should reset, and then the inverter should dip back down and trigger the forced
    cancel.
    """
    # Deploy proposal inverter
    owner = Wallet()
    owner.funds = 1000
    inverter = owner.deploy(100, min_brokers=2, broker_whitelist=NoVote())

    # Add brokers
    broker1 = inverter.add_broker(broker1, 10)
    broker2 = inverter.add_broker(broker2, 10)

    assert inverter.funds == 100
    assert inverter.stake == 20
    assert inverter.get_horizon() >= inverter.min_horizon

    # Dip below minimum conditions but before the forced cancel triggers
    inverter.iter_epoch(6)

    assert inverter.get_horizon() < inverter.min_horizon
    assert inverter.get_allocated_funds() < inverter.funds

    # Add a second broker and funds to meet the minimum conditions again
    payer = inverter.pay(payer, 60)

    assert inverter.number_of_brokers() >= inverter.min_brokers
    assert inverter.get_horizon() >= inverter.min_horizon

    inverter.iter_epoch(6)

    assert inverter.get_horizon() < inverter.min_horizon
    assert inverter.get_allocated_funds() < inverter.funds


def test_owner_whitelist(owner, broker1, payer):
    inverter = owner.deploy(500, broker_whitelist=OwnerVote())

    # Broker applies to proposal, but not yet whitelisted
    broker1 = inverter.add_broker(broker1, 10)

    assert broker1.funds == 100
    assert inverter.number_of_brokers() == 0

    # Owner adds broker to whitelist
    inverter.vote_broker(owner, broker1, True)
    broker1 = inverter.add_broker(broker1, 10)

    assert broker1.funds == 90
    assert inverter.number_of_brokers() == 1

    # Owner removes broker from whitelist
    inverter.vote_broker(owner, broker1, False)
    broker1 = inverter.remove_broker(broker1)

    assert broker1.funds == 90
    assert inverter.number_of_brokers() == 0

    # Broker tries to apply to proposal again after being removed from whitelist
    broker1 = inverter.add_broker(broker1, 10)

    assert broker1.funds == 90
    assert inverter.number_of_brokers() == 0
