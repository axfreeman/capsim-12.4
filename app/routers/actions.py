from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.schemas import IndustryBase
from ..simulation.reload import reload_table, initialise_buyers_and_sellers
from ..database import get_db
from ..simulation.demand import (
    class_demand,
    commodity_demand,
    initialise_demand,
    industry_demand,
)
from ..simulation.supply import initialise_supply, industry_supply, class_supply
from ..simulation.trade import buy_and_sell, constrain_demand
from ..simulation.production import production, social_class_reproduce
from ..authorization.auth import get_current_simulation
from ..models import (
    Simulation,
    Stock,
    SocialClass,
    Industry,
    Commodity,
    Trace,
)

router = APIRouter(prefix="/action", tags=["Actions"])


# initialise demand and supply
@router.get("/demand")
def set_demand_and_supply(
    session: Session = Depends(get_db),
    simulation: Simulation = Depends(get_current_simulation),
):
    print("Set Demand requested by authenticated user")
    # TODO if there are no simulations, action buttons should be greyed out
    if (simulation==None):
        return "No Simulations Available"
    initialise_demand(
        session, simulation, 0
    )  # test to see if it worked by putting 2 in the db. TODO remember to set this back to 0
    industry_demand(
        session, simulation
    )  # tell industries to register their demand and supply with their stocks
    class_demand(
        session, simulation
    )  # tell classes to register their demand and supply with their stocks
    commodity_demand(
        session, simulation
    )  # tell the commodities to tot up the demand from all stocks of them
    return "Demand initialized"


@router.get("/supply")
def set_supply(
    session: Session = Depends(get_db),
    simulation: Simulation = Depends(get_current_simulation),
):
    # TODO if there are no simulations, action buttons should be greyed out
    if (simulation==None):
        return "No Simulations Available"

    initialise_supply(
        session, simulation, 0
    )  # test to see if it worked by putting 2 in the db. TODO remember to set this back to 0
    industry_supply(
        session, simulation
    )  # tell industries to register their demand and supply with their stocks
    class_supply(
        session, simulation
    )  # tell classes to register their demand and supply with their stocks
    # tell the commodities to tot up the demand from all stocks of them (note supply was set directly)
    return "Supply initialized"


# TODO check if demand has been set? This may be necessary to forestall user trying to do them in the wrong order
# TODO code to ensure that buyers and sellers have been created - though the user will not have control over this so it's just a preventitive anti-bug measure
@router.get("/trade")
def trade(
    session: Session = Depends(get_db),
    simulation: Simulation = Depends(get_current_simulation),
):
    # TODO if there are no simulations, action buttons should be greyed out
    if (simulation==None):
        return "No Simulations Available"
    constrain_demand(session, simulation)
    buy_and_sell(session, simulation)
    return "Trading complete"


@router.get("/produce")
def produce(
    session: Session = Depends(get_db),
    simulation: Simulation = Depends(get_current_simulation),
):
    # TODO if there are no simulations, action buttons should be greyed out
    if (simulation==None):
        return "No Simulations Available"
    production(session, simulation)
    return "Prduction and social reproduction complete"


# TODO confine this to a specific simulation
@router.get("/reset")
def get_json(session: Session = Depends(get_db)):
    # TODO as a quick fix, we are initialising with simulation_id=1.
    # TODO this should be an action only available to the admin and will reinitialise everything
    # TODO once we have the login and authorization working, each user will be able to initialize their own simulation only
    reload_table(session, Simulation, "static/simulations.json", True, 1)
    reload_table(session, SocialClass, "static/classes.json", True, 1)
    reload_table(session, Commodity, "static/commodities.json", True, 1)
    reload_table(session, Industry, "static/industries.json", True, 1)
    # reload_table(session, SocialStocks, "static/class_stocks.json", True, 1)
    # reload_table(session, IndustryStocks, "static/industry_stocks.json", True, 1)
    reload_table(session, Stock, "static/stocks.json", True, 1)
    reload_table(session, Trace, "Trace table: no reload required", False, 1)

    initialise_buyers_and_sellers(
        session, 1
    )  # at this time, just initialise simulation 1

    return "Database reloaded"
