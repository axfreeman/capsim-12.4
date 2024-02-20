from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from ..authorization.auth import get_current_simulation
from typing import List
from ..database import get_db
from ..models import Simulation, Stock
from ..schemas import stocksBase


router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/", response_model=List[stocksBase])
def find_stocks(
    session: Session = Depends(get_db),
    simulation: Simulation = Depends(get_current_simulation),
):
    if simulation == None:
        return []
    return session.query(Stock).filter(Stock.simulation_id == simulation.id)


# get one stock
@router.get("/stock/{id}")
def get_stock(id: str, db: Session = Depends(get_db)):
    industry_stock = db.query(Stock).filter(Stock.id == int(id)).first()
    return industry_stock
