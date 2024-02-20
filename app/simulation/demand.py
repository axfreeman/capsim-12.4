from .. import models
from ..models import Commodity,Industry,SocialClass, Stock
from .logging import report

# Tell all commodities to initialise demand to zero
def initialise_demand(session,simulation,test_value):# 'test_value' is purely diagnostic. It should normally be zero
    report(1,simulation.id, "INITIALISING DEMAND FOR COMMODITIES AND STOCKS",session)
    cquery = session.query(Commodity).where(Commodity.simulation_id==simulation.id)
    for c in cquery:
        report(2,simulation.id,f"Initialising demand for commodity {c.name}",session)
        session.add(c)
        c.demand=test_value
    squery = session.query(Stock)
    for s in squery:
        report(2,simulation.id,f"Initialising demand for stock {s.name}",session)
        session.add(s)
        s.demand=test_value

    session.commit()

# Tell each industry to set demand for each of its productive stocks
def industry_demand(session,simulation):
    query=session.query(Industry).where(Industry.simulation_id==simulation.id)
    report(1,simulation.id, "CALCULATING DEMAND FROM INDUSTRIES",session)
    for industry in query:
        report(2, simulation.id,f"Industry {industry.name} will set demand for all its productive stocks",session)
        session.add(industry)
        query=session.query(Stock).filter(Stock.owner_id==industry.id,Stock.usage_type=="Production")
        for stock in query:
            session.add(stock)
            commodity=stock.commodity(session)
            demand=industry.output_scale*commodity.turnover_time*stock.requirement/simulation.periods_per_year 
            stock.demand+=demand #TODO - stock.size
            report(3,simulation.id,f'Demand for {stock.name} of {commodity.name} has been increased by {demand} to {stock.demand}',session)

    session.commit()

# tell each class to set demand for each of its consumption stocks
def class_demand(session,simulation):
    report(1,simulation.id, "CALCULATING DEMAND FROM SOCIAL CLASSES",session)
    query=session.query(SocialClass).where(SocialClass.simulation_id==simulation.id)
    for socialClass in query:
        report(2, simulation.id,f"Asking class {socialClass.name} to set demand for all its consumption stocks",session)
        session.add(socialClass)
        query=session.query(Stock).filter(Stock.owner_id==socialClass.id).filter(Stock.usage_type=="Consumption")
        for stock in query:
            report(3,simulation.id,f"Processing consumption stock {stock.id}",session)
            session.add(stock)
            commodity=stock.commodity(session)
            demand=socialClass.population*socialClass.consumption_ratio*stock.requirement/simulation.periods_per_year
            stock.demand+=demand #TODO size
            report(3,simulation.id,f'Demand for {stock.name} of {commodity.name} has been increased by {demand} to {stock.demand}',session)

    session.commit()


# for each commodity, add up the total demand by asking all its stocks what they need
# do this separately from the stocks as a kind of check - could be done at the same time
def commodity_demand(session,simulation):
    report(1,simulation.id,"ADDING UP DEMAND FOR COMMODITIES",session)
    query=session.query(models.Commodity).where(Commodity.simulation_id==simulation.id)
    for commodity in query:
        session.add(commodity)
        report(1,simulation.id, f'Calculating total demand for {commodity.name}',session)
        d=0
        squery=session.query(Stock).filter(Stock.commodity_id==commodity.id)
        for stock in squery:
            owner=stock.owner(session)
            report(2,simulation.id,f'Demand for {commodity.name} from {stock.name} with owner id ({stock.owner_id}) is {stock.demand}',session)
            d+=stock.demand
        report (1,simulation.id, f'Total demand for {commodity.name} is now {d}',session)
        commodity.demand=d

    session.commit()


