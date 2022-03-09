import numpy as np

from .funds import Funds
from .proposal_inverter import Wallet


rng = np.random.default_rng(42)


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
