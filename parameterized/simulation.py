import numpy as np
import pandas as pd
import plotly.express as px

from cadCAD import configs
from cadCAD.configuration import Experiment
from cadCAD.configuration.utils import config_sim
from cadCAD.engine import Executor, ExecutionContext, ExecutionMode

import actions
import hyperparameters
import policies
import state_updates

from proposal_inverter import Wallet


rng = np.random.default_rng(42)
pd.options.plotting.backend = "plotly"


initial_state = {
    # Initial conditions of the system
    "total_funds": 500_000,
    "wallet_funds": 500_000,
    "proposal_funds": 0,
    "n_wallets": 50,
    "n_proposals": 0,

    # Global variables
    "wallets": dict(),
    "proposals": dict(),
    "transactions": list(), # columns=["timestep", "wallet", "wallet_funds", "action", "proposal", "proposal_funds"]
    
    # Distribution of agent actions
    "join": 0,
    "claim": 0,
    "leave": 0,
    "pay": 0,
    "vote": 0,
    "deploy": 0,
    "cancel": 0,
    
    # Proposal properties
    "funds_staked": 0,
    "funds_claimed": 0,
    "funds_contributed": 0,
}


funds_distribution = rng.random(size=initial_state["n_wallets"])
funds_distribution = funds_distribution / np.sum(funds_distribution) * initial_state["total_funds"]

for funds in funds_distribution:
    wallet = Wallet(funds={"USD": funds})
    wallet.feature_vector = rng.uniform(size=wallet.number_of_features)

    initial_state["wallets"][wallet.public] = wallet
    initial_state["transactions"].append({
        "timestep": 0,
        "wallet": wallet.public,
        "wallet_funds": wallet.funds.total_funds(),
        "action": "initialize",
    })


system_params = {
    "feature_noise": [hyperparameters.h_feature_noise],
    
    # Probabilities defining the action space
    "join": [actions.a_decreasing_linear],
    "claim": [actions.a_dynamic_joined],
    "leave": [actions.a_static_1_percent],
    "pay": [actions.a_increasing_linear],
    "vote": [actions.a_dynamic_funded],
    "deploy": [actions.a_normal],
    "cancel": [actions.a_static_0_percent],
    
    # The hyperparameters of each action
    "join_stake": [hyperparameters.h_join_stake],

    "pay_contribution": [hyperparameters.h_pay_contribution],

    "vote_broker": [hyperparameters.h_vote_broker],
    "vote_result": [hyperparameters.h_vote_result],
    
    "deploy_initial_funds": [hyperparameters.h_deploy_initial_funds],

    "global": [["wallets", "proposals", "transactions"]],
}


partial_state_update_blocks = [
    # Go to next epoch
    {
        "policies": {
            "free_memory": policies.p_free_memory,
            "iter_epoch": policies.p_iter_epoch,
            "iter_features": policies.p_iter_features,
        },
        "variables": {
        },
    },
    {   
        # Agents perform actions
        "policies": {
            "join": policies.p_join,
            "claim": policies.p_claim,
            "leave": policies.p_leave,
            "pay": policies.p_pay,
            "vote": policies.p_vote,
            "deploy": policies.p_deploy,
            "cancel": policies.p_cancel,
        },
        'variables': {
            "transactions": state_updates.s_transactions,
            "total_funds": state_updates.s_total_funds,
            "wallet_funds": state_updates.s_wallet_funds,
            "proposal_funds": state_updates.s_proposal_funds,
            "n_proposals": state_updates.s_n_proposals,

            "funds_staked": state_updates.s_funds_staked,
            "funds_claimed": state_updates.s_funds_claimed,
            "funds_contributed": state_updates.s_funds_contributed,
        }
    }
]

sim_configs = config_sim({
    "N": 1, #the number of Monte Carlo runs
    "T": range(100), # the number of timesteps per run
    "M": system_params, # parameters of the system
})

experiment = Experiment()
experiment.append_configs(
    initial_state=initial_state,
    partial_state_update_blocks=partial_state_update_blocks,
    sim_configs=sim_configs,
)

exec_context = ExecutionContext()
simulation = Executor(exec_context=exec_context, configs=configs)
raw_result, tensor_field, sessions = simulation.execute()

transactions = pd.DataFrame(raw_result[-1]["transactions"])
transactions.to_csv("transactions.csv", header=True, index=False)
