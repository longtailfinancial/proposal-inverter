import numpy as np

from proposal_inverter import Wallet


rng = np.random.default_rng(42)


def a_static_0_percent(wallet: Wallet, wallets: dict, proposals: dict) -> list[bool]:
    """Returns `True` with a probability of 0%. In other words, `False` with a probability of 100%."""
    return np.full(shape=len(proposals), fill_value=False)


def a_static_1_percent(wallet: Wallet, wallets: dict, proposals: dict) -> list[bool]:
    """Returns `True` with a probability of 1%."""
    return rng.uniform(size=len(proposals)) < 0.01


def a_static_50_percent(wallet: Wallet, wallets: dict, proposals: dict) -> list[bool]:
    """Returns `True` with a probability of 50%."""
    return rng.uniform(size=len(proposals)) < 0.5


def a_static_100_percent(wallet: Wallet, wallets: dict, proposals: dict) -> list[bool]:
    """Returns `True` with a probability of 100%."""
    return np.full(shape=len(proposals), fill_value=True)


def a_dynamic_joined(wallet: Wallet, wallets: dict, proposals: dict, pr: float) -> list[bool]:
    """Returns `True` with a specified probability for all proposals this wallet has joined."""
    return np.array([
        rng.random() < pr 
        if wallet.public in proposal.broker_agreements.keys() 
        else False 
        for proposal in proposals.values()
    ])


def a_dynamic_funded(wallet: Wallet, wallets: dict, proposals: dict, pr: float) -> list[bool]:
    """Returns `True` with a specified probability for all proposals this wallet has funded."""
    return np.array([
        rng.random() < pr 
        if wallet.public in proposal.payer_agreements.keys() 
        else False 
        for proposal in proposals.values()
    ])


def a_decreasing_linear(wallet: Wallet, wallets: dict, proposals: dict, y_scale: float=1) -> list[bool]:
    """Based on a linear distribution where lower funds means a higher probability of joining."""
    max_funds = np.max([w.funds.total_funds() for w in wallets.values()])
    pr = y_scale * (-wallet.funds.total_funds() / max_funds + 1)
    
    return rng.uniform(size=len(proposals)) < pr


def a_increasing_linear(wallet: Wallet, wallets: dict, proposals: dict, y_scale: float=1) -> list[bool]:
    """Based on a linear distribution where higher funds means a higher probability of paying."""
    max_funds = np.max([w.funds.total_funds() for w in wallets.values()])
    pr = y_scale * (wallet.funds.total_funds() / max_funds)
    
    return rng.uniform(size=len(proposals)) < pr


def a_normal(wallet: Wallet, wallets: dict, proposals: dict, y_scale: float=1) -> list[bool]:
    """Based on a normal Gaussian distribution with the mean funds as the centre."""
    mean_funds = np.mean([w.funds.total_funds() for w in wallets.values()])
    max_funds = np.max([w.funds.total_funds() for w in wallets.values()])
    pr = y_scale * np.exp(-0.5 * np.power((wallet.funds.total_funds() - mean_funds) / (max_funds / 3), 2))
    
    return rng.uniform(size=1) < pr


def a_probability(wallet: Wallet, wallets: dict, proposals: dict, y_scale: float=1) -> list[bool]:
    """Based on the highest probability from the result of matrix factorization."""
    p_matrix = [
        proposal.feature_vector 
        for proposal in proposals.values() 
        if not proposal.cancelled
    ]
    prs = np.matmul(p_matrix, wallet.feature_vector)

    return rng.uniform(size=len(proposals)) < prs
    