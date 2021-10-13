from proposal_inverter import Owner, Broker


def test_deploy_proposal_inverter():
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(500)

    assert inverter.funds == 500
    assert inverter.current_epoch == 0
    assert inverter.number_of_brokers() == 0


def test_remove_proposal_inverter():
    # Deploy proposal inverter
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(500)
    
    # Add brokers (each with a different initial stake)
    broker1 = Broker()
    broker2 = Broker()
    broker1.funds = 100
    broker2.funds = 100
    broker1 = inverter.add_broker(broker1, 50)
    broker2 = inverter.add_broker(broker2, 100)
    
    # Check total funds: 500(owner initial amount) + 50 (broker1 stake) + 100 (broker2 stake)
    assert inverter.funds == 650
    
    inverter.iter_epoch(30)
    
    # Create a prototype broker pool, which is a dictionary where the key is the broker public key
    # and the value is the broker object
    broker_pool = {
        broker1.public: broker1,
        broker2.public: broker2,
    }
    
    """
    If we have a proposal inverter deployed at 500 and 2 brokers enter the agreement, 
    broker 1 (stake=50) & broker2 (stake=100), enter at epoch=0, at epoch=30, 
    each of their claimable funds would be 150. 
    Broker 1 should receive: 50 + 150 + (650-1(150)-50-100)/2 = 50 + 150 +100 =300 
    Broker 2 should receive: 100 + 150 + (650-1(150)-50-100)/2 = 50 + 150 +100 =350
    """
    for public_key, broker_agreement in inverter.broker_agreements.items():
        assert broker_agreement.allocated_funds == 150
        
    # Call the cancel function which returns the updated broker pool
    broker_pool = owner.cancel(inverter, broker_pool)
    
    # Broker1 funds = 300 + 50(broker1's current funds)
    assert broker1.funds == 350
    
    # Broker2 funds = 350 + 0(broker2's current funds)
    assert broker2.funds == 350

