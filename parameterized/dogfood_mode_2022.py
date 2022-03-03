import pytest

from .proposal_inverter import Wallet, ProposalInverter
from .whitelist_mechanism import OwnerVote


def test_dogfood_model_2022():
    """This is the dogfood model of the plan for 2022.

    PrimeDAO is the owner, and GitCoin and the TEC are payers, each
    contributing $15 000.

    There are 10 brokers to start with, each joining with a nominal stake of
    $1.

    Each epoch is one month long, the minimum horizon is two months, and the
    allocation per month is $20 000. This means that there should always be a
    minimum of $40 000 in the proposal at all times.
    """
    primedao = Wallet(funds=15_000)
    gitcoin = Wallet(funds=15_000)
    tec = Wallet(funds=15_000)

    brokers = [Wallet(funds=1) for _ in range(10)]

    proposal = primedao.deploy(
        initial_funds=15_000,
        min_stake=1,
        min_epochs=1,
        min_horizon=2,
        epoch_length=3600*24*30,
        allocation_per_epoch=20_000,
        max_brokers=20,
        broker_whitelist=OwnerVote(),
    )

    proposal.pay(gitcoin, 15_000)
    proposal.pay(tec, 15_000)

    for broker in brokers:
        proposal.vote_broker(primedao, broker, True)
        broker = proposal.add_broker(broker=broker, stake=1)

    assert proposal.funds == 45_000
    assert proposal.number_of_brokers() == 10

    proposal.iter_epoch()

    for broker in brokers:
        broker = proposal.claim_broker_funds(broker)
        assert broker.funds == 2_000

    assert proposal.funds == 25_000
