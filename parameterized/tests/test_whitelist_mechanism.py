import pytest

from parameterized.proposal_inverter import Wallet, ProposalInverter
from parameterized.whitelist_mechanism import NoVote, OwnerVote, PayerVote, EqualVote, WeightedVote, UnanimousVote


@pytest.fixture
def owner():
    owner = Wallet()
    owner.funds = 500

    return owner


@pytest.fixture
def payer1():
    payer1 = Wallet()
    payer1.funds = 500

    return payer1


@pytest.fixture
def payer2():
    payer2 = Wallet()
    payer2.funds = 500

    return payer2


@pytest.fixture
def inverter(owner, payer1, payer2):
    inverter = owner.deploy(300)
    payer1 = inverter.pay(payer1, 200)
    payer2 = inverter.pay(payer2, 100)
    
    return inverter


@pytest.fixture
def broker():
    broker = Wallet()
    broker.funds = 100

    return broker


def test_no_vote(owner, payer1, inverter, broker):
    mechanism = NoVote()

    # Votes should not impact whitelisting, and should whitelist all brokers
    mechanism.vote(inverter, payer1, broker, False)

    assert mechanism.in_waitlist(broker) == False
    assert mechanism.in_whitelist(broker) == True


def test_owner_vote(owner, payer1, inverter, broker):
    mechanism = OwnerVote()

    # Case where payer cannot whitelist a broker
    mechanism.vote(inverter, payer1, broker, True)

    assert mechanism.in_waitlist(broker) == False
    assert mechanism.in_whitelist(broker) == False

    # Case where only the owner can whitelist a broker
    mechanism.vote(inverter, owner, broker, True)

    assert mechanism.in_waitlist(broker) == False
    assert mechanism.in_whitelist(broker) == True


def test_payer_vote(payer1, payer2, inverter, broker):
    mechanism = PayerVote()

    # Case where any payer can whitelist a broker and override a blacklist vote
    mechanism.vote(inverter, payer1, broker, False)

    assert mechanism.in_waitlist(broker) == True
    assert mechanism.in_whitelist(broker) == False

    mechanism.vote(inverter, payer2, broker, True)

    assert mechanism.in_waitlist(broker) == False
    assert mechanism.in_whitelist(broker) == True


def test_equal_vote(payer1, payer2, inverter, broker):
    mechanism = EqualVote(min_vote=0.5)

    mechanism.vote(inverter, payer1, broker, True)

    assert mechanism.in_waitlist(broker) == True
    assert mechanism.in_whitelist(broker) == False

    mechanism.vote(inverter, payer2, broker, True)

    assert mechanism.in_waitlist(broker) == False
    assert mechanism.in_whitelist(broker) == True


def test_weighted_vote(payer1, payer2, inverter, broker):
    mechanism = WeightedVote(min_vote=0.6)

    # Case where two voters do not have enough combined funds
    mechanism.vote(inverter, payer1, broker, True)
    mechanism.vote(inverter, payer2, broker, True)

    assert mechanism.in_waitlist(broker) == True
    assert mechanism.in_whitelist(broker) == False

    # Case where a payer increases their funds to increase their weight
    payer1 = inverter.pay(payer1, 200)

    mechanism.vote(inverter, payer1, broker, True)

    assert mechanism.in_waitlist(broker) == False
    assert mechanism.in_whitelist(broker) == True


def test_unanimous_vote(owner, payer1, payer2, inverter, broker):
    mechanism = UnanimousVote()

    print(mechanism.waitlist)
    print(mechanism.whitelist)

    mechanism.vote(inverter, payer1, broker, True)

    print(mechanism.waitlist)
    print(mechanism.whitelist)
    
    mechanism.vote(inverter, payer2, broker, True)

    print(mechanism.waitlist)
    print(mechanism.whitelist)

    assert mechanism.in_waitlist(broker) == True
    assert mechanism.in_whitelist(broker) == False    

    mechanism.vote(inverter, owner, broker, True)

    assert mechanism.in_waitlist(broker) == False
    assert mechanism.in_whitelist(broker) == True
