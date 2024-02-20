# Utility to merge social stocks and industry stocks and produce a single stocks table
from pydantic import EmailStr
from sqlalchemy import insert
from ..database import get_db
from fastapi import Depends, APIRouter
from ..models import Simulation, Stock, Industry, Commodity, SocialClass, SocialStocks,IndustryStocks
from typing import List
from sqlalchemy.orm import Session
from ..schemas import stocksBase


router = APIRouter(prefix="/fixes", tags=["Fixes"])

# Constructs an amalgamated Stocks table from former (discarded) Industry and Class stock tables
# this then has to be accessed using Swagger or some such, and downloaded, to be copied into the amalgamated stock json file
# Stocks owned by classes
@router.get("/buildStocks", response_model=List[stocksBase])
def merge_stocks(session: Session = Depends(get_db)):
    query = session.query(Stock)
    query.delete(synchronize_session=False)

    sstocks = session.query(SocialStocks)

    for stock in sstocks:
        newStock = [
            {
                "id":stock.id,
                "name": stock.owner(session).name+"."+stock.commodity(session).name+"."+stock.usage_type+"."+str(stock.simulation_id),
                "simulation_id": stock.simulation_id,
                "commodity_id": stock.commodity_id,
                "owner_id": stock.owner_id,
                "owner_type": "Class",
                "usage_type": stock.usage_type,
                "size": stock.size,
                "requirement": stock.requirement,
                "demand": stock.demand,
            }
        ]
        session.execute(insert(Stock), newStock)

    istocks = session.query(IndustryStocks)
    for stock in istocks:
        newStock = [
            {
                "id":stock.id,
                "name":  stock.owner(session).name+"."+stock.commodity(session).name+"."+stock.usage_type+"."+str(stock.simulation_id),
                "simulation_id": stock.simulation_id,
                "commodity_id": stock.commodity_id,
                "owner_id": stock.owner_id,
                "owner_type": "Industry",
                "usage_type": stock.usage_type,
                "size": stock.size,
                "requirement": stock.requirement,
                "demand": stock.demand,
            }
        ]
        session.execute(insert(Stock), newStock)
    session.commit()
    stocks = session.query(Stock)
    return stocks

# @router.post("/upload")
# def upload_file(file: UploadFile = File(...), response_model=schemas.UploadIn):
#     print(f"file name is {file}")
#     if file.content_type != "application/json":
#         raise HTTPException(400, detail="Invalid document type")
#     else:
#         data = json.loads(file.file.read())
#         print(data)
#     return {"content": data} 

def loadFromStorage(db: Session)->[]:
    query = db.query(Simulation)
#   for simulation in query:
#     print(simulation.name)     
    return query.all()

def interrogate_results():
    global simulations
    print(simulations)

# Utility to calculate the price and value of all stock items
# and generate an API endpoint so we can create a new fixture.
# Also recalculate commodity total value and total price (though not strictly necessary)
    
@router.get("/fixStocks", response_model=List[stocksBase])
def fix_stocks(session: Session = Depends(get_db)):
    print("Entering fix stocks")
    commodity_query=session.query(Commodity)#.where(Commodity.usage!='MONEY')
    for commodity in commodity_query:
        print("Processing a commodity")

        session.add(commodity)
        commodity.total_value=0
        commodity.total_price=0
        commodity.size=0
    print("done with commodities")
    stocks_query = session.query(Stock)#.where(Stock.usage_type!='Money')
    for stock in stocks_query:
        print("Processing a stock")
        session.add(stock)
        commodity=stock.commodity(session)
        session.add(commodity)
        stock.value=stock.size*stock.commodity(session).unit_value
        stock.price=stock.size*stock.commodity(session).unit_price
        commodity.size+=stock.size
        commodity.total_value+=stock.value
        commodity.total_price+=stock.price
    print("done with stocks")
    session.commit()

    stocks=session.query(Stock).where(Stock.simulation_id==1)

    return stocks
