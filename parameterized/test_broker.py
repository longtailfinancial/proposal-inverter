from proposal_inverter import Owner, Broker, ProposalInverter


def test_deploy_proposal_inverter():
    owner = Owner()
    owner.funds = 1000
    inverter = owner.deploy(500)

    assert inverter.funds == 500
    assert inverter.current_epoch == 0
    assert inverter.number_of_brokers() == 0


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

