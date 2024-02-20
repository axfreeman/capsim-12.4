from .. import models
from ..models import Commodity,Industry,SocialClass, Stock, Simulation
from .logging import report
from sqlalchemy.orm import Session

# Tell all commodities to initialise demand to zero
def initialise_demand(db: Session,simulation: Simulation,test_value):# TODO 'test_value' was an early diagnostic. It can be removed
    """
    Sets demand for all stocks in a simulation.
    First, initialise demand to zero
    Ask every industry to calculate demand for its productive stocks
    Ask every social class to calculate consumer demand
    Tell every commodity to add up demand from stocks of it
    """
    report(1,simulation.id, "INITIALISING DEMAND FOR COMMODITIES AND STOCKS",db)
    cquery = db.query(Commodity).where(Commodity.simulation_id==simulation.id)
    for c in cquery:
        report(2,simulation.id,f"Initialising demand for commodity {c.name}",db)
        db.add(c)
        c.demand=test_value
    squery = db.query(Stock)
    for s in squery:
        report(2,simulation.id,f"Initialising demand for stock {s.name}",db)
        db.add(s)
        s.demand=test_value

    db.commit()

def industry_demand(db:Session,simulation:Simulation):
    """
    Tell each industry to set demand for each of its productive stocks
    """
    query=db.query(Industry).where(Industry.simulation_id==simulation.id)
    report(1,simulation.id, "CALCULATING DEMAND FROM INDUSTRIES",db)
    for industry in query:
        report(2, simulation.id,f"Industry {industry.name} will set demand for all its productive stocks",db)
        db.add(industry)
        query=db.query(Stock).filter(Stock.owner_id==industry.id,Stock.usage_type=="Production")
        for stock in query:
            db.add(stock)
            commodity=stock.commodity(db)
            demand=industry.output_scale*commodity.turnover_time*stock.requirement/simulation.periods_per_year 
            stock.demand+=demand #TODO - stock.size
            report(3,simulation.id,f'Demand for {stock.name} of {commodity.name} has been increased by {demand} to {stock.demand}',db)

    db.commit()

def class_demand(db:Session,simulation:Simulation):
    """
    Tell each class to set demand for each of its consumption stocks
    """
    report(1,simulation.id, "CALCULATING DEMAND FROM SOCIAL CLASSES",db)
    query=db.query(SocialClass).where(SocialClass.simulation_id==simulation.id)
    for socialClass in query:
        report(2, simulation.id,f"Asking class {socialClass.name} to set demand for all its consumption stocks",db)
        db.add(socialClass)
        query=db.query(Stock).filter(Stock.owner_id==socialClass.id).filter(Stock.usage_type=="Consumption")
        for stock in query:
            report(3,simulation.id,f"Processing consumption stock {stock.id}",db)
            db.add(stock)
            commodity=stock.commodity(db)
            demand=socialClass.population*socialClass.consumption_ratio*stock.requirement/simulation.periods_per_year
            stock.demand+=demand #TODO size
            report(3,simulation.id,f'Demand for {stock.name} of {commodity.name} has been increased by {demand} to {stock.demand}',db)

    db.commit()


def commodity_demand(db:Session,simulation:Simulation):
    """
    for each commodity, add up the total demand by asking all its stocks what they need
    do this separately from the stocks as a kind of check - could be done at the same time
    """
    report(1,simulation.id,"ADDING UP DEMAND FOR COMMODITIES",db)
    query=db.query(models.Commodity).where(Commodity.simulation_id==simulation.id)
    for commodity in query:
        db.add(commodity)
        report(1,simulation.id, f'Calculating total demand for {commodity.name}',db)
        d=0
        squery=db.query(Stock).filter(Stock.commodity_id==commodity.id)
        for stock in squery:
            owner=stock.owner(db)
            report(2,simulation.id,f'Demand for {commodity.name} from {stock.name} with owner id ({stock.owner_id}) is {stock.demand}',db)
            d+=stock.demand
        report (1,simulation.id, f'Total demand for {commodity.name} is now {d}',db)
        commodity.demand=d

    db.commit()


