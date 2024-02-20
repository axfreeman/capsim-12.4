from fastapi import Cookie, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List
from ..authorization.auth import get_current_simulation
from ..database import get_db
from ..models import Commodity, Simulation
from ..schemas import CommodityBase

router = APIRouter(prefix="/commodities", tags=["Commodity"])


# Get all commodities in the simulation of the logged-in user
# In the special case of the admin user, the initial batch of simulations all have id=1
# These also function as 'templates' for the user to choose between, and appear in the user dashboard
@router.get("/", response_model=List[CommodityBase])
def get_commodities(
    db: Session = Depends(get_db),
    simulation: Simulation = Depends(get_current_simulation),
):
    if simulation == None:
        return []
    commodities = db.query(Commodity).where(Commodity.simulation_id == simulation.id)
    return commodities


# get one commodity
@router.get("/{id}")
def get_commodity(id: str, db: Session = Depends(get_db)):
    commodity = db.query(Commodity).filter(Commodity.id == int(id)).first()
    return commodity
