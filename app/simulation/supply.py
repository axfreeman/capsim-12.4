from .. import models
from ..models import Commodity,Industry,SocialClass, Stock
from .logging import report

# Tell all commodities to initialise supply to zero
def initialise_supply(session,simulation,test_value):# 'test_value' is purely diagnostic. It should normally be zero
    cquery = session.query(Commodity).where(Commodity.simulation_id==simulation.id)
    for c in cquery:
        report(1,simulation.id,f"Initialising commodity {c.name}",session)
        session.add(c)
        c.supply=test_value
    squery = session.query(Stock)
    for s in squery:
        session.add(s)
        s.supply=test_value

    session.commit()

# Ask each industry to tell its output commodity how much it has to sell
def industry_supply(session,simulation):
    print(f"Calculating supply for simulation {simulation.id}")
    query=session.query(Industry).where(Industry.simulation_id==simulation.id)
    report(1,simulation.id, "CALCULATING SUPPLY FOR INDUSTRIES",session)
    for industry in query:
        sales_stock=industry.sales_stock(session)
        commodity=sales_stock.commodity(session)
        print(f"Debugging supply by industry {industry.name} and id {industry.id}")
        print(f"Processing sales stock with name {sales_stock.name} and id {sales_stock.id}")
        print(f"The commodity of this stock is {commodity.name} and its ID is {commodity.id}")
        session.add(commodity) # session.add(sales_stock) # not needed because we are not changing the stock
        ns=sales_stock.size 
        report(2,simulation.id,f'{industry.name} adds {ns:.0f} to the supply of {commodity.name}, which was previously {commodity.supply:.0f}',session)
        commodity.supply+=ns
      
    session.commit()

# Ask each industry to tell its output commodity how much it has to sell
def class_supply(session,simulation):
    report(1,simulation.id, "CALCULATING SUPPLY FROM SOCIAL CLASSES",session)
    query=session.query(SocialClass).where(SocialClass.simulation_id==simulation.id)
    for socialClass in query:
        sales_stock=socialClass.sales_stock(session)
        commodity=sales_stock.commodity(session) # commodity that this owner supplies
        session.add(commodity)
        ns=sales_stock.size 
        report(2,simulation.id,f'{socialClass.name} adds {ns:.0f} to the supply of {commodity.name}, which was previously {commodity.supply:.0f}',session)  
        commodity.supply+=ns

    session.commit()
