from proposal_inverter import Owner, Broker, ProposalInverter
    
    
def test_add_broker():
    # Deploy proposal inverter
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(500)

    # Add broker to proposal inverter
    broker = Broker()
    broker.funds = 100

    broker = inverter.add_broker(broker, 50)

    assert inverter.funds == 550
    assert inverter.number_of_brokers() == 1

    assert broker.funds == 50


def test_claim_broker_funds():
    # Deploy proposal inverter
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(500)

    # Add broker to proposal inverter
    broker1 = Broker()
    broker1.funds = 100

    broker1 = inverter.add_broker(broker1, 50)

    # Make a claim before the minimum number of epochs
    inverter.iter_epoch(10)

    broker1 = inverter.claim_broker_funds(broker1)

    assert inverter.funds == 450
    assert broker1.funds == 150

    # Add a second broker
    broker2 = Broker()
    broker2.funds = 100

    broker2 = inverter.add_broker(broker2, 50)

    # Make a claim before the minimum number of epochs
    inverter.iter_epoch(10)

    broker2 = inverter.claim_broker_funds(broker2)

    assert inverter.funds == 450
    assert broker2.funds == 100

    # Make a claim after the minimum number of epochs
    inverter.iter_epoch(10)

    broker1 = inverter.claim_broker_funds(broker1)

    assert inverter.funds == 350
    assert broker1.funds == 250

    
def test_remove_broker():
    # Deploy proposal inverter
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(500)

    # Add brokers
    broker1 = Broker()
    broker2 = Broker()

    broker1.funds = 100
    broker2.funds = 100
    
    broker1 = inverter.add_broker(broker1, 100)
    broker2 = inverter.add_broker(broker2, 100)

    assert inverter.number_of_brokers() == 2
    assert inverter.funds == 700

    # Remove a broker while over the minimum horizon
    inverter.iter_epoch(30)

    broker1 = inverter.remove_broker(broker1)

    assert inverter.number_of_brokers() == 1
    assert inverter.funds == 550
    assert broker1.funds == 150

    
def test_get_allocated_funds():
    # Deploy proposal inverter
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(500)

    assert inverter.get_allocated_funds() == 0

    # Add broker
    broker1 = Broker()
    broker1.funds = 100
    broker1 = inverter.add_broker(broker1, 100)

    # Add a second broker
    inverter.iter_epoch(10)

    broker2 = Broker()
    broker2.funds = 100
    broker2 = inverter.add_broker(broker2, 100)

    assert inverter.funds == 700
    assert inverter.number_of_brokers() == 2
    assert inverter.get_allocated_funds() == 100

    inverter.iter_epoch(20)

    assert inverter.get_allocated_funds() == 300


def test_pay():
    # Deploy proposal inverter
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(500)

    payer = Broker()
    payer.funds = 100

    payer = inverter.pay(payer, 25)

    assert payer.funds == 75
    assert inverter.funds == 525

    
def test_cancel():
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
    
    # Cancel the proposal inverter
    inverter.cancel()

    # Each broker makes their claim
    broker1 = inverter.claim_broker_funds(broker1)
    broker2 = inverter.claim_broker_funds(broker2)
        
    # Broker1 funds = 300 + 50(broker1's current funds)
    assert broker1.funds == 350
    
    # Broker2 funds = 350 + 0(broker2's current funds)
    assert broker2.funds == 350

    # End state of proposal inverter
    assert inverter.funds == 0
    assert inverter.get_allocated_funds() == 0

    
def test_forced_cancel_case1():
    """
    First test case involves using an inverter where the minimum number of brokers is 2. If only one broker joins and
    the minimum horizon is reached, then the forced cancel should be triggered and all remaining funds should be
    allocated to the single broker in the inverter.
    """
    # Deploy proposal inverter
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(100, min_brokers=2)

    # Add broker
    broker = Broker()
    broker.funds = 100

    broker = inverter.add_broker(broker, 10)

    # Iterate past the buffer period to trigger the forced cancel
    inverter.iter_epoch(10)

    assert inverter.number_of_brokers() < inverter.min_brokers
    assert inverter.get_horizon() < inverter.min_horizon
    assert inverter.get_allocated_funds() == inverter.funds


def test_forced_cancel_case2():
    """
    Second test case occurs when the inverter is below the minimum horizon and all brokers leave. In this case, there
    are no brokers to allocate the funds to, so when the forced cancel is triggered, all funds should be returned to the
    owner.
    """
    # Deploy proposal inverter
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(100)

    # Add broker
    broker = Broker()
    broker.funds = 100

    broker = inverter.add_broker(broker, 9)

    # Dip below the minimum conditions
    inverter.iter_epoch(5)

    broker = inverter.remove_broker(broker)

    # Iterate past the buffer period
    inverter.iter_epoch(6)

    assert inverter.number_of_brokers() < inverter.min_brokers
    assert inverter.get_horizon() < inverter.min_horizon
    assert inverter.get_allocated_funds() == inverter.funds


def test_forced_cancel_case3():
    """
    Third test case is to ensure the forced cancel counter resets if the inverter is no longer under the minimum
    conditions. The inverter dips below the minimum conditions for a few epochs less than the specified buffer period,
    and the goes back up. The counter should reset, and then the inverter should dip back down and trigger the forced
    cancel.
    """
    # Deploy proposal inverter
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(100, min_brokers=2)

    # Add brokers
    broker1 = Broker()
    broker1.funds = 100

    broker1 = inverter.add_broker(broker1, 10)

    # Dip below minimum conditions but before the forced cancel triggers
    inverter.iter_epoch(6)

    assert inverter.number_of_brokers() < inverter.min_brokers
    assert inverter.get_horizon() < inverter.min_horizon
    assert inverter.get_allocated_funds() < inverter.funds

    # Add a second broker and funds to meet the minimum conditions again
    broker2 = Broker()
    broker2.funds = 100

    broker2 = inverter.add_broker(broker2, 60)

    assert inverter.number_of_brokers() >= inverter.min_brokers
    assert inverter.get_horizon() >= inverter.min_horizon

    # Dip below minimum conditions and trigger the forced cancel
    broker1 = inverter.remove_broker(broker1)

    inverter.iter_epoch(6)

    assert inverter.number_of_brokers() < inverter.min_brokers
    assert inverter.get_horizon() < inverter.min_horizon
    assert inverter.get_allocated_funds() < inverter.funds

    inverter.iter_epoch(4)

    assert inverter.get_allocated_funds() == inverter.funds

