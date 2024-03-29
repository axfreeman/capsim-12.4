"""This module handles 'actions', each of which takes the 
simulation one step through the circuit.

Once an action is complete it resets the state of the simulation
to the next stage of the circuit. 

The user implements an action by pressing a button on the main
menuu. The simulation state is used to ensure that the user can
only undertake the correct action in the circuit, so they proceed
in sequence.

TODO prevent the user implementing an action by entering its URL.
"""

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
from ..simulation.invest import invest
from ..authorization.auth import User, get_current_user_and_simulation, usPair
from ..models import (
    Class_stock,
    Industry_stock,
    Simulation,
    SocialClass,
    Industry,
    Commodity,
    Trace,
)
from ..simulation.utils import calculate_current_capitals, recalculate_commodity_totals, revalue_stocks, revalue_commodities

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

# Reset commodity demand from stock demands
        
    commodity_demand(db,u.simulation)

# Reset commodity supply from industry and class supplies
# TODO there may be some duplication in the code for supply

    initialise_supply(db, u.simulation)
    industry_supply(db, u.simulation)  # tell industries to register their supply
    class_supply(db, u.simulation)  # tell classes to register their supply 

    # TODO I don't think it's necessary to also to revalue, but check.
    # It should not be necessary, because trade only involves a change of ownership.
    # If it is necessary, we should probably implement the line below.

    # revalue_stocks(db,u.simulation) 

    return "Trading complete"

@router.get("/produce")
def produceHandler(
    db: Session = Depends(get_db),
    u: usPair = Depends(get_current_user_and_simulation),
)->str:
    """
    Handles calls to the 'Produce' action then resets simulation state
    to the next in the circuit.

    Assumes that get_current_user() has handled any errors. 
    Therefore does not check u except to decide whether or not to go ahead. 

    Once Production and Consumption are both complete, we will 
    recalculate unit values and prices and then revalue all Stocks.

    This separate calculation cannot done inside production, because
    in order to revise unit values and prices, Social Classes must first
    restore their sale_stocks. Otherwise there is an apparent net loss 
    of Labour Power and it will be overvalued.

    At this stage, we *do* recalculate the total size, value and price of
    every commodity in existence but do not revise values and prices in 
    accordance with the resultant change in unit values and prices.

    And we *do* calculate the new current capital, profits, and profit 
    rates to demonstrate the independent effect of production on these
    magnitudes.

    This has to be recalculated, however, after consumption because if 
    the industries have stocks of labour power on hand, and there has been
    a change in the value of labour power (for example due to a wage increase)
    their stocks will be revalued accordingly, changing their profits.
    """

    if u.user is None or u.simulation is None or u.simulation.state=="TEMPLATE": 
        return None

    produce(db, u.simulation)
    db.add(u.simulation)
    u.simulation.state = "CONSUME"
    db.commit()

# Recalculate commodity totals (but do not revalue or reprice)
    
    recalculate_commodity_totals(db,u.simulation)

# Recalculate current capital and profit

    calculate_current_capitals(db,u.simulation)
    return "Production complete"

@router.get("/consume")
def consumeHandler(
    db: Session = Depends(get_db),
    u: usPair = Depends(get_current_user_and_simulation),
)->str:
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
    recalculate_commodity_totals()
    revalue_commodities(db,u.simulation)
    # Then recalculate the price and value of every stock
    revalue_stocks(db, u.simulation)
    calculate_current_capitals(db,u.simulation)
    return "Consumption complete"

@router.get("/invest")
def investHandler(
    db: Session = Depends(get_db),
    u: usPair = Depends(get_current_user_and_simulation),
)->str:
    """Handles calls to the 'Invest' action then resets simulation state
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
    invest(u.simulation,db)
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
