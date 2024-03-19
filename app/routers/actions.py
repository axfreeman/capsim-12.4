from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.simulation.consumption import consume

from ..simulation.logging import report
from ..simulation.reload import reload_table
from ..database import get_db
from ..simulation.demand import (
    class_demand,
    commodity_demand,
    initialise_demand,
    industry_demand,
)
from ..simulation.supply import initialise_supply, industry_supply, class_supply
from ..simulation.trade import buy_and_sell, constrain_demand
from ..simulation.production import produce
from ..authorization.auth import User, get_current_user_and_simulation, usPair
from ..models import (
    Class_stock,
    Industry_stock,
    Simulation,
    Stock,
    SocialClass,
    Industry,
    Commodity,
    Trace,
)
from ..simulation.utils import calculate_current_capitals, revalue_stocks, revalue_commodities

router = APIRouter(prefix="/action", tags=["Actions"])

@router.get("/demand")
def demandHandler(
    db: Session = Depends(get_db),
    u:usPair = Depends(get_current_user_and_simulation)
)->str:
    """
    Handles calls to the 'Demand' action. Sets demand, then resets the 
    simulation state to the next in the circuit. 

    Assumes that get_current_user() has handled any errors. 
    Therefore does not check u except to decide whether or not to go ahead. 
    """
    if u.user is None or u.simulation is None or u.simulation.state=="TEMPLATE": 
        return None
    
    initialise_demand(db, u.simulation)
    industry_demand(db, u.simulation) # tell industries to register their demand with their stocks.
    class_demand(db, u.simulation)  # tell classes to register their demand with their stocks.
    commodity_demand(db, u.simulation)  # tell the commodities to tot up the demand from all stocks of them.
    db.add(u.simulation)
    u.simulation.state = "SUPPLY" # set the next state in the circuit, obliging the user to do this next.
    db.commit()
    return "Demand initialised"

@router.get("/supply")
def supplyHandler(
    db: Session = Depends(get_db),
    u: usPair = Depends(get_current_user_and_simulation),
):
    """Handles calls to the 'Supply' action. Sets supply, then resets 
    simulation state to the next in the circuit.

    Assumes that get_current_user() has handled any errors. 

    Therefore does not check u except to decide whether or not to go ahead. 
    """
    if u.user is None or u.simulation is None or u.simulation.state=="TEMPLATE": 
        return None
    initialise_supply(db, u.simulation)
    industry_supply(db, u.simulation)  # tell industries to register their supply
    class_supply(db, u.simulation)  # tell classes to register their supply 
    # tell the commodities to tot up supply from all stocks of them (note supply was set directly)
    db.add(u.simulation)
    u.simulation.state = "TRADE"
    db.commit()
    return "Supply initialised"

@router.get("/trade")
def tradeHandler(
    db: Session = Depends(get_db),
    u: usPair = Depends(get_current_user_and_simulation),
):
    """
    Handles calls to the 'Trade' action. Allocates supply, conducts 
    trade, and resets simulation state to the next in the circuit.

    Receives a 'usPair' object from get_current_user_and_simulation to
    make life easier.

    Assumes that get_current_user() has handled any errors. 
    Therefore does not check u except to decide whether or not to go ahead. 
    """
    if u.user is None or u.simulation is None or u.simulation.state=="TEMPLATE": 
        return None

    constrain_demand(db, u.simulation)
    buy_and_sell(db, u.simulation)
    db.add(u.simulation)
    u.simulation.state = "CONSUME"
    db.commit()
    # TODO I don't think it's necessary to revalue, but check.
    # This is because trade only involves a change of ownership.
    # revalue_stocks(db,u.simulation) 
    return "Trading complete"

@router.get("/produce")
def produceHandler(
    db: Session = Depends(get_db),
    u: usPair = Depends(get_current_user_and_simulation),
):
    """
    Handles calls to the 'Produce' action then resets simulation state
    to the next in the circuit.

    Assumes that get_current_user() has handled any errors. 
    Therefore does not check u except to decide whether or not to go ahead. 
    """
    if u.user is None or u.simulation is None or u.simulation.state=="TEMPLATE": 
        return None

    produce(db, u.simulation)
    db.add(u.simulation)
    u.simulation.state = "CONSUME"
    db.commit()

    # Don't revalue yet, because consumption (social reproduction) has to
    # be complete before all the facts are in. 
    calculate_current_capitals(db,u.simulation)
    return "Production complete"

@router.get("/consume")
def consumeHandler(
    db: Session = Depends(get_db),
    u: usPair = Depends(get_current_user_and_simulation),
):
    """
    Handles calls to the 'Consume' action then resets simulation state
    to the next in the circuit.

    Instructs every social class to consume and reproduce anything it sells.

    Assumes that get_current_user() has handled any errors. 

    Therefore does not check u except to decide whether or not to go ahead. 
    """
    if u.user is None or u.simulation is None or u.simulation.state=="TEMPLATE": 
        return None

    consume(db, u.simulation)
    db.add(u.simulation)
    u.simulation.state = "INVEST"
    db.commit()
    revalue_commodities(db,u.simulation)
    # Then recalculate the price and value of every stock
    revalue_stocks(db, u.simulation)
    calculate_current_capitals(db,u.simulation)
    return "Consumption complete"

@router.get("/invest")
def investHandler(
    db: Session = Depends(get_db),
    u: usPair = Depends(get_current_user_and_simulation),
):
    """
    Handles calls to the 'Invest' action then resets simulation state
    to the next in the circuit.

    Instructs every industry to assess whether it has a money surplus
    over and above what would be needed to produce at the same level as
    it has just been doing.

    If so, attempt to raise the output_scale by the minimum of what
    this money will pay for, and the growth rate.

    Note that if the means are not available to make this possible, in
    the demand stage of the next circuit, output will be scaled down.

    This is only one of a number of possible algorithms.
    
    Assumes that get_current_user() has handled any errors. 

    Therefore does not check u except to decide whether or not to go ahead. 
    """
    report(1,u.simulation.id,"INVESTING", db)
    industries=db.query(Industry).where(Industry.simulation_id==u.simulation.id)
    for industry in industries:
        report(3,u.simulation.id,"Transferring profit to the capitalists as revenue",db)
        # TODO calculate private consumption
        capitalists=db.query(SocialClass).where(SocialClass.simulation_id==u.simulation.id).first() # for now suppose just one propertied class
        private_capitalist_consumption = capitalists.consumption_ratio*industry.profit
        report(3,u.simulation.id,f"Industry {industry.name} will transfer {private_capitalist_consumption} of its profit to its owners",db)
        cms =capitalists.money_stock(db)
        ims=industry.money_stock(db)
        print("Capitalist money stock",cms.id, cms.name)
        print("Industry money stock",ims.id,ims.name)
        db.add(cms)
        db.add(ims)
        cms.size+=private_capitalist_consumption
        cms.value=cms.size # TODO for now suppose MELT is 1
        cms.price=cms.size
        ims.size-=private_capitalist_consumption
        ims.value=ims.size # TODO for now suppose MELT is 1
        ims.price=ims.size
        db.commit()
        report(3,u.simulation.id,f"Capitalists now have a money stock of {capitalists.money_stock(db).size}",db)
        report(3,u.simulation.id,f"Industry {industry.name} now has a money stock of {industry.money_stock(db).size}",db)
        report(2,u.simulation.id,"Estimating the output scale which can be financed",db)
        cost=industry.unit_cost(db)*industry.output_scale
        report(3,u.simulation.id,f"Industry {industry.name} has unit cost {industry.unit_cost(db)} so needs to spend {cost} to produce at the same scale.",db)
        spare=industry.money_stock(db).size-cost
        report(3,u.simulation.id,f"It has {industry.money_stock(db).size} to spend and so can invest {spare}",db)
        possible_increase=spare/industry.unit_cost(db)
        monetarily_potential_growth=possible_increase/cost
        if monetarily_potential_growth>industry.output_growth_rate:
            attempted_new_scale=industry.output_scale*(1+industry.output_growth_rate)
        else:
            attempted_new_scale=industry.output_scale*(1+monetarily_potential_growth)
        report(3,u.simulation.id,f"Setting output scale, which was {industry.output_scale}, to {attempted_new_scale}",db)
        industry.output_scale=attempted_new_scale
    u.simulation.state = "DEMAND"
    db.commit()
    return "Investment decision-making complete"

@router.get("/reset")
def get_json(db: Session = Depends(get_db)):
    """
    Reloads all tables in the simulation from json fixtures
    Logs out all users and sets their current simulation to 0
    TODO this action should only be available to the admin 
    TODO since it reinitialises everything
    """
    report(1,1,"RESETTING ENTIRE DATABASE",db)
    reload_table(db, Simulation, "static/simulations.json", True, 1)
    reload_table(db, SocialClass, "static/classes.json", True, 1)
    reload_table(db, Commodity, "static/commodities.json", True, 1)
    reload_table(db, Industry, "static/industries.json", True, 1)
    reload_table(db, Class_stock, "static/class_stocks.json", True, 1)
    reload_table(db, Industry_stock, "static/industry_stocks.json", True, 1)
    reload_table(db, Stock, "static/stocks.json", True, 1)
    reload_table(db, Trace, "Trace table: no reload required", False, 1)

    # Reset all users to default status
    for user in db.query(User).all():
        db.add(user)
        user.current_simulation=0
        user.is_logged_in=0

    # Set the username in all simulations to be "admin"
    # TODO improve on this bodge
    for simulation in db.query(Simulation).all():
        db.add(simulation)
        simulation.username="admin"
    db.commit()
    return "Database reloaded"
