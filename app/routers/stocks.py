from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from ..authorization.auth import get_current_simulation
from typing import List
from ..database import get_db
from ..models import Class_stock, Industry_stock, Simulation
from ..schemas import Class_stock_base, Industry_stock_base

router = APIRouter(prefix="/stocks", tags=["Stocks"])

@router.get("/industry", response_model=List[Industry_stock_base])
def find_industry_stocks(
    db: Session = Depends(get_db),
    simulation: Simulation = Depends(get_current_simulation),
):
    """Get all industry stocks in one simulation.
    Return empty list if simulation is None."""
    if simulation == None:
        return []
    return db.query(Industry_stock).filter(Industry_stock.simulation_id == simulation.id)

@router.get("/industry/{id}")
def get_stock(id: str, db: Session = Depends(get_db)):
    """Get one industry stock with the given id."""
    return db.query(Industry_stock).filter(Industry_stock.id == int(id)).first()

@router.get("/class", response_model=List[Class_stock_base])
def find_class_stocks(
    db: Session = Depends(get_db),
    simulation: Simulation = Depends(get_current_simulation),
):
    """Get all class stocks in one simulation.
    Return empty list if simulation is None"""
    if simulation == None:
        return []
    return db.query(Class_stock).filter(Class_stock.simulation_id == simulation.id)

@router.get("/class/{id}")
def get_stock(id: str, db: Session = Depends(get_db)):
    """Get one class stock with the given id."""
    return db.query(Class_stock).filter(Class_stock.id == int(id)).first()

