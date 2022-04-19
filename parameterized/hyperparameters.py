import numpy as np

from scipy.stats import norm

from .funds import Funds
from .proposal_inverter import Wallet, ProposalInverter


rng = np.random.default_rng(42)


def h_wallet_feature_0(wallets: dict):
    mean, std_dev = norm.fit(
        [wallet.funds.total_funds() for wallet in wallets.values()]
    )

    feature = norm.cdf(
        x=[wallet.funds.total_funds() for wallet in wallets.values()],
        loc=mean,
        scale=std_dev,
    )

    return feature


def h_proposal_feature_0(proposals: dict):
    return np.ones(shape=len(proposals))


def h_proposal_feature_1(proposals: dict):
    mean, std_dev = norm.fit(
        [proposal.funds.total_funds() for proposal in proposals.values()]
    )

    feature = norm.cdf(
        x=[proposal.funds.total_funds() for proposal in proposals.values()],
        loc=mean,
        scale=std_dev,
    )

    return feature


def h_proposal_feature_2(proposals: dict):
    mean, std_dev = norm.fit(
        [proposal.current_epoch for proposal in proposals.values()]
    )

    feature = norm.cdf(
        x=[proposal.current_epoch for proposal in proposals.values()],
        loc=mean,
        scale=std_dev,
    )

    return feature


def h_proposal_feature_3(proposals: dict):
    mean, std_dev = norm.fit(
        [proposal.get_horizon() for proposal in proposals.values()]
    )

    feature = norm.cdf(
        x=[proposal.get_horizon() for proposal in proposals.values()],
        loc=mean,
        scale=std_dev,
    )

    return feature


def h_proposal_feature_4(proposals: dict):
    mean, std_dev = norm.fit(
        [proposal.allocation_per_epoch for proposal in proposals.values()]
    )

    feature = norm.cdf(
        x=[proposal.allocation_per_epoch for proposal in proposals.values()],
        loc=mean,
        scale=std_dev,
    )

    return feature


def h_join_stake(wallet: Wallet, wallets: dict) -> Funds:
    return Funds({"USD": 10})


def h_pay_contribution(wallet: Wallet, wallets: dict) -> Funds:
    return Funds({"USD": 50})


def h_vote_broker(wallet: Wallet, wallets: dict) -> int:
    return rng.choice(list(wallets.keys()))


def h_vote_result(wallet: Wallet, wallets: dict) -> bool:
    return True


def h_deploy_initial_funds(wallet: Wallet, wallets: dict) -> Funds:
    return Funds({"USD": 100})
