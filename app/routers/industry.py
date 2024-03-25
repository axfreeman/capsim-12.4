from fastapi import status, Depends, APIRouter
from sqlalchemy.orm import Session

from ..authorization.auth import get_current_simulation
from typing import List
from ..database import get_db
from ..models import Simulation, Industry
from ..schemas import IndustryBase

router = APIRouter(prefix="/industries", tags=["Industry"])



@router.get("/", response_model=List[IndustryBase])
def get_Industries(
    session: Session = Depends(get_db),
    simulation: Simulation = Depends(get_current_simulation),
):
    """Get all Industries"""
    # TODO  this should (1) allow the admin user to see all items (2) allow the admin user to filter by user
    if simulation == None:
        return []
    Industries = session.query(Industry).where(Industry.simulation_id == simulation.id)
    return Industries


# get one Industry
@router.get("/{id}")
def get_Industry(id: str, session: Session = Depends(get_db)):
    Industry = session.query(Industry).filter(Industry.id == int(id)).first()
    return Industry
