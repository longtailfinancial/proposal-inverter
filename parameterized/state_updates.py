from .funds import Funds


def s_transactions(params, substep, state_history, previous_state, policy_input):
    return "transactions", previous_state["transactions"] + policy_input["transactions"]


def s_total_funds(params, substep, state_history, previous_state, policy_input):
    wallet_funds = sum([wallet.funds for wallet in previous_state["wallets"].values()], Funds())
    proposal_funds = sum([proposal.funds + proposal.stake for proposal in previous_state["proposals"].values()], Funds())
    
    return "total_funds", wallet_funds.total_funds() + proposal_funds.total_funds()


def s_wallet_funds(params, substep, state_history, previous_state, policy_input):
    return "wallet_funds", sum([wallet.funds for wallet in previous_state["wallets"].values()], Funds()).total_funds()


def s_proposal_funds(params, substep, state_history, previous_state, policy_input):
    return "proposal_funds", sum([proposal.funds for proposal in previous_state["proposals"].values()], Funds()).total_funds()


def s_n_proposals(params, substep, state_history, previous_state, policy_input):
    return "n_proposals", len(previous_state["proposals"])


def s_funds_staked(params, substep, state_history, previous_state, policy_input):
    funds_staked = previous_state["funds_staked"] + policy_input["funds_staked"]
    
    return "funds_staked", funds_staked


def s_funds_claimed(params, substep, state_history, previous_state, policy_input):
    funds_claimed = previous_state["funds_claimed"] + policy_input["funds_claimed"]
    
    return "funds_claimed", funds_claimed


def s_funds_contributed(params, substep, state_history, previous_state, policy_input):
    funds_contributed = previous_state["funds_contributed"] + policy_input["funds_contributed"]
    
    return "funds_contributed", funds_contributed
