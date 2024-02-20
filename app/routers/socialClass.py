from fastapi import   Depends, APIRouter
from sqlalchemy.orm import Session
from ..authorization.auth import get_current_simulation
from typing import List
from ..database import  get_db
from ..models import SocialClass,Simulation
from ..schemas import SocialClassBase

router=APIRouter(
    prefix="/classes",
    tags=['Class']
)

# get all socialClasses
#TODO  this should (1) only retrieve the items assigned to the logged in user (2) allow the admin user to see all items (3) allow the admin user to filter by user
@router.get("/",response_model=List[SocialClassBase])
def get_socialClasses(db: Session = Depends (get_db),simulation:Simulation=Depends(get_current_simulation)):
    if (simulation==None):
        return []
    socialClasses=db.query(SocialClass).where(SocialClass.simulation_id==simulation.id)
    return socialClasses

# get one Social Class
#TODO restrict to current simulation
@router.get("/{id}")
def get_socialClass(id:str,db: Session=Depends(get_db)):    
    socialClass=db.query(SocialClass).filter(SocialClass.id==int(id)).first()
    return socialClass

