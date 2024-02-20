from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List
from ..authorization.auth import get_current_simulation
from ..database import  get_db
from ..models import Commodity,Simulation
from ..schemas import CommodityBase

router=APIRouter(
    prefix="/commodities",
    tags=['Commodity']
)

# get all commodities
#TODO  this should (1) allow the admin user to see all items (2) allow the admin user to filter by user
@router.get("/",response_model=List[CommodityBase])
def get_commodities(db: Session = Depends (get_db),simulation:Simulation=Depends(get_current_simulation)):
    if (simulation==None):
        return []
    commodities=db.query(Commodity).where(Commodity.simulation_id==simulation.id)
    return commodities

# get one commodity
@router.get("/{id}")
def get_commodity(id:str,db: Session=Depends(get_db)):    
    commodity=db.query(Commodity).filter(Commodity.id==int(id)).first()
    return commodity

