from fastapi import  status, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

from app.authorization.auth import AuthHandler
from app.authorization.authroutes import Authentication_handler
from app.simulation.logging import report
from ..database import  get_db
from ..models import Simulation, User
from ..schemas import AuthDetails, SimulationOut,SimulationCreate


router=APIRouter(
    prefix="/simulations",
    tags=['Simulation']
)

# Provide a list of Template simulations, to be used to create actual simulations
@router.get("/templates",response_model=List[SimulationOut])
def get_simulations(db: Session = Depends (get_db),username=Depends(Authentication_handler.auth_wrapper)):
    report(1,1,f"User {username} wants to see templates",db) # ALL simulations of type TEMPLATE
    simulations=db.query(Simulation).filter(Simulation.state=="TEMPLATE")
    return simulations

# get one simulation
@router.get("/by_id/{id}")
def get_simulation(id:str,db: Session=Depends(get_db)):    
    simulation=db.query(Simulation).filter(Simulation.id==int(id)).first()
    return simulation

# Provide a list of simulations owned by the logged-in user
@router.get("/mine",response_model=List[SimulationOut])
def get_simulations(db: Session = Depends (get_db),username=Depends(Authentication_handler.auth_wrapper)):
    report(1,1,f"I am {username} and I want to see my simulations",db)
    me=db.query(User).filter(User.username==username).first() # TODO is a mistake possible? Test for it      
    simulations=db.query(Simulation).filter(Simulation.user_id==me.id)
    return simulations
