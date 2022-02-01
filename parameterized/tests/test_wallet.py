from parameterized.proposal_inverter import Wallet
from parameterized.whitelist_mechanism import NoVote


def test_deploy_proposal_inverter():
    owner = Wallet()
    owner.funds = 1000
    inverter = owner.deploy(500, broker_whitelist=NoVote())

    assert inverter.funds == 500
    assert inverter.current_epoch == 0
    assert inverter.number_of_brokers() == 0


def test_remove_proposal_inverter():
    # Deploy proposal inverter
    owner = Wallet()
    owner.funds = 1000
    inverter = owner.deploy(500, broker_whitelist=NoVote())
    
    # Add brokers (each with a different initial stake)
    broker1 = Wallet()
    broker2 = Wallet()
    broker1.funds = 100
    broker2.funds = 100
    broker1 = inverter.add_broker(broker1, 50)
    broker2 = inverter.add_broker(broker2, 100)
    
    # Check total funds: 500(owner initial amount)
    assert inverter.funds == 500
    assert inverter.stake == 150
    assert broker1.funds == 50
    assert broker2.funds == 0
    
    inverter.iter_epoch(30)
    
    """
    If we have a proposal inverter deployed at 500 and 2 brokers enter the
    agreement, broker 1 (stake=50) & broker2 (stake=100), enter at epoch=0, at
    epoch=30, each of their claimable funds would be 150. 

    Broker 1 should receive: 50 + 150 + (500 - (2 * 150)) / 2 = 300 
    Broker 2 should receive: 100 + 150 + (500 - (2 * 150)) / 2 = 350
    """
    for public_key, broker_agreement in inverter.broker_agreements.items():
        assert broker_agreement.allocated_funds == 150
        
    # Call the cancel function and remove brokers
    inverter.cancel(owner.public)
    broker1 = inverter.remove_broker(broker1)
    broker2 = inverter.remove_broker(broker2)
    
    # Broker1 funds = 300 + 50 (broker1's current funds)
    assert broker1.funds == 350
    
    # Broker2 funds = 350 + 0 (broker2's current funds)
    assert broker2.funds == 350
