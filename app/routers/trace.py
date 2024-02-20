from fastapi import  Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List
from ..authorization.auth import get_current_simulation
from ..database import  get_db
from ..models import Simulation,Trace
from ..schemas import TraceOut


router=APIRouter(
    prefix="/trace",
    tags=['Trace']
)

# get all trace records
@router.get("/",response_model=List[TraceOut])
def get_trace(db: Session = Depends (get_db),simulation:Simulation=Depends(get_current_simulation)):
    if (simulation==None):
        return []
    trace=db.query(Trace).where(Trace.simulation_id==simulation.id)
    return trace
