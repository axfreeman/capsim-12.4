from fastapi import  status, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List
from app.authorization.auth import get_current_user_and_simulation, get_current_simulation
from app.simulation.logging import report
from ..database import  get_db
from ..models import Simulation, Commodity,Industry,SocialClass, Stock, Trace
from ..authorization.auth import User, usPair
from ..schemas import  SimulationBase


router=APIRouter(
    prefix="/simulations",
    tags=['Simulation']
)

@router.get("/",response_model=List[SimulationBase])
def get_simulations(db: Session = Depends (get_db)):
    """Retrieve all Simulation objects in the system.
    Not protected because it is not sensitive.
    TODO think about security implications if any.
    """
    simulations=db.query(Simulation).all()
    return simulations

@router.get("/templates",response_model=List[SimulationBase])
def get_simulations(db: Session = Depends (get_db)):
    """Retrieve all templates. 
    These are used to create actual simulations.
    This is not protected because it is not sensitive.
    TODO think about security implications if any.
    """
    # report(1,1,f"Request to retrieve templates",db) 
    simulations=db.query(Simulation).filter(Simulation.state=="TEMPLATE")
    return simulations


@router.get("/by_id/{id}")
def get_simulation(id:str,db: Session=Depends(get_db)):    
    """Get one simulation.
    Currently protected, but not sure if this is needed.
    TODO think about security implications if any.
    """
    simulation=db.query(Simulation).filter(Simulation.id==int(id)).first()
    return simulation

@router.get("/mine",response_model=List[SimulationBase])
def get_simulations(db: Session = Depends (get_db),u:usPair=Depends(get_current_user_and_simulation)):
    """Replies with all simulations belonging to the logged-in user.
    Protected because we need to know which user's information to supply.
    """
    if u.user is None or u.simulation is None or u.simulation.state=="TEMPLATE": 
        return []

    # report(1,1,f"User {u.user.username} has asked for its simulations",db)
    simulations=db.query(Simulation).where(Simulation.user_id==u.user.id)
    return simulations

@router.get("/delete/{id}")
def delete_simulation(id:str,db: Session=Depends(get_db),u:usPair=Depends(get_current_user_and_simulation)):    
    """
    Delete the simulation with this id and all dependent objects
    Do it by hand rather than using cascade, because we don't
    want to be reliant on the cascade mechanism
    """
    if u.user is None or u.simulation is None or u.simulation.state=="TEMPLATE": 
        return None
    print(f"{u.user.username} wants to delete simulation {u.simulation}")
    if (u.simulation != None):
       db.delete(u.simulation)

    commodityQuery=db.query(Commodity).where(Commodity.simulation_id==int(id))
    for commodity in commodityQuery:
        db.delete(commodity)

    industryQuery=db.query(Industry).where(Industry.simulation_id==int(id))
    for industry in industryQuery:
        db.delete(industry)

    social_classQuery=db.query(SocialClass).where(SocialClass.simulation_id==int(id))
    for social_class in social_classQuery:
        db.delete(social_class)

    stockQuery=db.query(Stock).where(Stock.simulation_id==int(id))
    for stock in stockQuery:
        db.delete(stock)

    traceQuery=db.query(Trace).where(Trace.simulation_id==int(id))
    for trace in traceQuery:
        db.delete(trace)

    db.commit()
    return f"Simulation {id} deleted"
