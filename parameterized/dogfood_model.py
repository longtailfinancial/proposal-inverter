import pytest

from .proposal_inverter import Wallet, ProposalInverter
from .whitelist_mechanism import NoVote, OwnerVote

def owner():
    owner = Wallet()
    owner.funds = 1000

    return owner
    
def inverter(owner):
    inverter = owner.deploy(500, broker_whitelist=NoVote())

    return inverter
    
def broker1():
    broker1 = Wallet()
    broker1.funds = 100

    return broker1

def broker2():
    broker2 = Wallet()
    broker2.funds = 100

    return broker2
    
def broker3():
    broker3 = Wallet()
    broker3.funds = 100

    return broker3

def broker4():
    broker4 = Wallet()
    broker4.funds = 100

    return broker4
    
def payer():
    payer = Wallet()
    payer.funds = 100

    return payer

def use_case_test(owner, broker1, broker2, broker3, broker4, payer):
    """
    This test is a practical use case scenario for the proposal inverter. It is meant to put
    this project into pragmatic scenario by using an example where the proposal inverter iself
    is a pitched proposal, the PrimoDAO team as the owners, and the token engineering team hired
    to work on it as the brokers. The pay period for the brokers is 15 epochs. This example assumes
    that the brokers for the proposal inverter are staking 50 into the proposal, which is not necessarily
    indicative of what the actual brokers of the proposal inverter are doing.
    """
    
    # Shawn (Broker1), with funding of PrimeDAO (owner), launches the proposal inverter as a project, secures initial funding and stakes 50
    inverter = owner.deploy(1000, broker_whitelist=NoVote())
    broker1 = inverter.add_broker(broker1, 50)
    
    # The current funds for the proposal inverter is the deployed amount plus Shawn's (Broker1's) stake
    assert inverter.funds == 1050
    assert inverter.number_of_brokers() == 1
    
    # After a set amount of time, 2 new brokers, Taz (Broker2) and Austin(Broker3), are added to the proposal inverter (new hires)
    inverter.iter_epoch(10)
    broker2 = inverter.add_broker(broker2, 50)
    broker3 = inverter.add_broker(broker3, 50)
    
    # After the addition of 2 brokers, the number of brokers increases, and the funds increase due to the additional stakes
    assert inverter.funds == 1150
    assert inverter.number_of_brokers() == 3
    
    # After the first period elapses, the proposal is set for the next payment (either by an unknown invester/payer or PrimeDAO) if it's meeting expectations
    # The brokers can claim funds for the epochs spent working on the proposal
    inverter.iter_epoch(5)
    broker1 = inverter.claim_broker_funds(broker1)
    broker2 = inverter.claim_broker_funds(broker2)
    broker3 = inverter.claim_broker_funds(broker3)
    payer = inverter.pay(payer, 50)
    assert inverter.funds == 1050
    
    # The brokers continue working on the proposal inverter research project & the proposal is approved for it's next pay period
    inverter.iter_epoch(15)
    broker1 = inverter.claim_broker_funds(broker1)
    broker2 = inverter.claim_broker_funds(broker2)
    broker3 = inverter.claim_broker_funds(broker3)
    payer = inverter.pay(payer, 50)
    assert inverter.funds == 950
    
    # After a set amount of time, new broker, Tomas (Broker3), joins the proposal
    inverter.iter_epoch(10)
    broker4 = inverter.add_broker(broker4, 50)
    assert inverter.funds == 1000
    
    # After the proposal inverter project is complete, PrimeDAO closes the proposal
    inverter.cancel(owner.public)
    
    # Each broker makes their claim from the proposal as a result of the success of the proposal inverter
    broker1 = inverter.remove_broker(broker1)
    broker2 = inverter.remove_broker(broker2)
    broker3 = inverter.remove_broker(broker3)
    broker4 = inverter.remove_broker(broker4)
    
    # No funds remain as they are distributed amongst the brokers 
    assert inverter.funds == 0
