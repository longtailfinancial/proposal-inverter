import numpy as np

from scipy.stats import norm

from .whitelist_mechanism import NoVote


rng = np.random.default_rng(42)


def p_free_memory(params, substep, state_history, previous_state):
    """Destroys the memory of some objects in the last timestep.
    
    https://community.cadcad.org/t/working-with-large-objects/215/2
    """
    for global_variable in params["global"]:
        state = state_history[-1]
        
        for substate in state:
            substate[global_variable] = None
                
    return dict()


def p_iter_epoch(params, substep, state_history, previous_state):
    for proposal in previous_state["proposals"].values():
        proposal.iter_epoch()
        
    print(f"Epoch: {previous_state['timestep']}")
        
    return dict()


def p_iter_features(params, substep, state_history, previous_state):
    mean, std_dev = norm.fit([
        wallet.funds.total_funds() 
        for wallet in previous_state["wallets"].values()
    ])

    for wallet in previous_state["wallets"].values():
        wallet.feature_vector[0] = norm.cdf(
            x=wallet.funds.total_funds(),
            loc=mean,
            scale=std_dev,
        )
        
    for proposal in previous_state["proposals"].values():
        pass
        
    return dict()


def p_join(params, substep, state_history, previous_state):
    n_joined = 0
    funds_staked = 0
    transactions = list()
    
    for wallet in previous_state["wallets"].values():
        proposals = np.extract(
            params["join"](
                wallet, 
                previous_state["wallets"],
                previous_state["proposals"],
                y_scale=0.05,
            ), 
            list(previous_state["proposals"].values())
        )

        for proposal in proposals:
            stake = params["join_stake"](wallet, previous_state["wallets"])
            
            wallet_funds_old = wallet.funds.total_funds()
            proposal_funds_old = (proposal.funds + proposal.stake).total_funds()

            try:
                wallet = proposal.join(wallet, stake)
            except ValueError:
                continue

            wallet_funds_new = wallet.funds.total_funds()
            
            if wallet_funds_new != wallet_funds_old:
                transaction = {
                    "timestep": previous_state["timestep"],
                    "wallet": wallet.public,
                    "wallet_funds_old": wallet_funds_old,
                    "wallet_funds": wallet_funds_new,
                    "action": "join",
                    "proposal": proposal.public,
                    "proposal_funds_old": proposal_funds_old,
                    "proposal_funds": (proposal.funds + proposal.stake).total_funds(),
                }

                transactions.append(transaction)

                n_joined += 1
                funds_staked += wallet_funds_old - wallet_funds_new
            
    return {
        "n_joined": n_joined,
        "funds_staked": funds_staked,
        "transactions": transactions,
    }
            
    
def p_claim(params, substep, state_history, previous_state):
    n_claimed = 0
    funds_claimed = 0
    transactions = list()
    
    for wallet in previous_state["wallets"].values():
        proposals = np.extract(
            params["claim"](
                wallet, 
                previous_state["wallets"],
                previous_state["proposals"],
                1,
            ), 
            list(previous_state["proposals"].values())
        )

        for proposal in proposals:
            wallet_funds_old = wallet.funds.total_funds()
            proposal_funds_old = (proposal.funds + proposal.stake).total_funds()
            
            try:
                wallet = proposal.claim(wallet)
            except ValueError:
                "wallet unable to claim funds, proposal low on funds"
            wallet_funds_new = wallet.funds.total_funds()
            
            if wallet_funds_new != wallet_funds_old:
                transaction = {
                    "timestep": previous_state["timestep"],
                    "wallet": wallet.public,
                    "wallet_funds_old": wallet_funds_old,
                    "wallet_funds": wallet_funds_new,
                    "action": "claim",
                    "proposal": proposal.public,
                    "proposal_funds_old": proposal_funds_old,
                    "proposal_funds": (proposal.funds + proposal.stake).total_funds(),
                }

                transactions.append(transaction)

                n_claimed += 1
                funds_claimed += wallet_funds_new - wallet_funds_old
            
    return {
        "n_claimed": n_claimed,
        "funds_claimed": funds_claimed,
        "transactions": transactions,
    }


def p_leave(params, substep, state_history, previous_state):
    n_left = 0
    funds_claimed = 0
    transactions = list()
    
    for wallet in previous_state["wallets"].values():
        proposals = np.extract(
            params["leave"](
                wallet, 
                previous_state["wallets"],
                previous_state["proposals"],
            ),
            list(previous_state["proposals"].values())
        )

        for proposal in proposals:
            wallet_funds_old = wallet.funds.total_funds()
            proposal_funds_old = (proposal.funds + proposal.stake).total_funds()
            
            wallet = proposal.leave(wallet)
            wallet_funds_new = wallet.funds.total_funds()
            
            if wallet_funds_new != wallet_funds_old:
                transaction = {
                    "timestep": previous_state["timestep"],
                    "wallet": wallet.public,
                    "wallet_funds_old": wallet_funds_old,
                    "wallet_funds": wallet_funds_new,
                    "action": "leave",
                    "proposal": proposal.public,
                    "proposal_funds_old": proposal_funds_old,
                    "proposal_funds": (proposal.funds + proposal.stake).total_funds(),
                }

                transactions.append(transaction)

                n_left += 1
                funds_claimed += wallet_funds_new - wallet_funds_old
            
    return {
        "n_left": n_left,
        "funds_claimed": funds_claimed,
        "transactions": transactions,
    }


def p_pay(params, substep, state_history, previous_state):
    n_paid = 0
    funds_contributed = 0
    transactions = list()

    for wallet in previous_state["wallets"].values():
        proposals = np.extract(
            params["pay"](
                wallet, 
                previous_state["wallets"],
                previous_state["proposals"],
                y_scale=0.005,
            ),
            list(previous_state["proposals"].values())
        )

        for proposal in proposals:
            wallet_funds_old = wallet.funds.total_funds()
            proposal_funds_old = (proposal.funds + proposal.stake).total_funds()
            
            contribution = params["pay_contribution"](wallet, previous_state["wallets"])
            
            wallet = proposal.pay(wallet, contribution)
            wallet_funds_new = wallet.funds.total_funds()
            
            if wallet_funds_new != wallet_funds_old:
                transaction = {
                    "timestep": previous_state["timestep"],
                    "wallet": wallet.public,
                    "wallet_funds_old": wallet_funds_old,
                    "wallet_funds": wallet_funds_new,
                    "action": "pay",
                    "proposal": proposal.public,
                    "proposal_funds_old": proposal_funds_old,
                    "proposal_funds": (proposal.funds + proposal.stake).total_funds(),
                }

                transactions.append(transaction)

                n_paid += 1
                funds_contributed += wallet_funds_new - wallet_funds_old
    
    return {
        "n_paid": n_paid,
        "funds_contributed": funds_contributed,
        "transactions": transactions,
    }


def p_vote(params, substep, state_history, previous_state):
    n_voted = 0
    voted_yes = 0
    
    for wallet in previous_state["wallets"].values():
        proposals = np.extract(
            params["vote"](
                wallet, 
                previous_state["wallets"],
                previous_state["proposals"],
                1,
            ), 
            list(previous_state["proposals"].values())
        )

        for proposal in proposals:
            broker = previous_state["wallets"][params["vote_broker"](wallet, previous_state["wallets"])]
            result = params["vote_result"](wallet, previous_state["wallets"])
            
            proposal.vote_broker(wallet, broker, result)
            
            n_voted += 1
            voted_yes += result * 1
            
    return {
        "n_voted": n_voted,
        "voted_yes": voted_yes,
    }


def p_deploy(params, substep, state_history, previous_state):
    n_deployed = 0
    funds_contributed = 0
    transactions = list()
    
    for wallet in previous_state["wallets"].values():
        deploy = params["deploy"](
            wallet,
            previous_state["wallets"],
            previous_state["proposals"],
            y_scale=0.01,
        )

        if any(deploy):
            wallet_funds_old = wallet.funds.total_funds()
            initial_funds = params["deploy_initial_funds"](wallet, previous_state["wallets"])
            
            proposal = wallet.deploy(
                funds=initial_funds,
                broker_whitelist=NoVote(),
                feature_vector=rng.random(size=wallet.number_of_features)
            )
            
            if proposal is not None:
                previous_state["proposals"][proposal.public] = proposal
                
                transaction = {
                    "timestep": previous_state["timestep"],
                    "wallet": wallet.public,
                    "wallet_funds_old": wallet_funds_old,
                    "wallet_funds": wallet.funds.total_funds(),
                    "action": "deploy",
                    "proposal": proposal.public,
                    "proposal_funds_old": 0,
                    "proposal_funds": proposal.funds.total_funds(),
                }
            
                transactions.append(transaction)
            
                n_deployed += 1
                funds_contributed += initial_funds.total_funds()
        
    return {
        "n_deployed": n_deployed,
        "funds_contributed": funds_contributed,
        "transactions": transactions,
    }


def p_cancel(params, substep, state_history, previous_state):
    n_cancelled = 0
    n_left = 0
    transactions = list()
    
    for wallet in previous_state["wallets"].values():
        proposals = np.extract(
            params["cancel"](
                wallet, 
                previous_state["wallets"],
                previous_state["proposals"]
            ), 
            list(previous_state["proposals"].values())
        )

        for proposal in proposals:
            proposal_funds_old = (proposal.funds + proposal.stake).total_funds()
            
            proposal.cancel(wallet.public)
            
            for broker_public in list(proposal.broker_agreements.keys()):
                broker = previous_state["wallets"][broker_public]

                broker_funds_old = broker.funds.total_funds()
                broker = proposal.leave(broker)
                
                transaction = {
                    "timestep": previous_state["timestep"],
                    "wallet": broker,
                    "wallet_funds_old": broker_funds_old,
                    "wallet_funds": broker.funds.total_funds(),
                    "action": "leave",
                    "proposal": proposal,
                    "proposal_funds_old": proposal_funds_old,
                    "proposal_funds": proposal.funds.total_funds(),
                }
            
                transactions.append(transaction)
                
                n_left += 1
                
            n_cancelled += 1
            
    return {
        "n_cancelled": n_cancelled,
        "n_left": n_left,
        "transactions": transactions,
    }
