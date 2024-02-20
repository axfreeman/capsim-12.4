from fastapi import  status, Depends, APIRouter
from sqlalchemy.orm import Session

from ..authorization.auth import get_current_simulation
from typing import List
from ..database import  get_db
from ..models import Commodity,Simulation, Buyer, Seller
from ..schemas import CommodityBase, BuyerBase, SellerBase

router=APIRouter(
    prefix="/buysell",
    tags=['Buyers and Sellers']
)

# get all buyers
@router.get("/buyers",response_model=List[BuyerBase])
def get_buyers(db: Session = Depends (get_db),simulation:Simulation=Depends(get_current_simulation)):
    if (simulation==None):
        return None
    buyers=db.query(Buyer).where(Buyer.simulation_id==simulation.id)
    return buyers

# get all sellers
@router.get("/sellers",response_model=List[SellerBase])
def get_sellers(db: Session = Depends (get_db),simulation:Simulation=Depends(get_current_simulation)):
    if (simulation==None):
        return None
    sellers=db.query(Seller).where(Seller.simulation_id==simulation.id)
    return sellers

