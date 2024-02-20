from .. import models
from ..models import Commodity,Industry, Simulation,SocialClass, Stock
from .logging import report
from sqlalchemy.orm import Session


"""
Helper functions for use in all parts of the simulation
"""

def revalue_commodities(db:Session, simulation:Simulation):
  """Calculate the size, value and price of all commodities from stocks
  of them.

  Recalculate unit values and unit prices on this basis.

  Normally, 'revalue stocks' should be called after this, because a change
  in the unit value and/or price will affect all stocks of it.
  """

  report(1,simulation.id,"CALCULATE THE SIZE, VALUE AND PRICE OF ALL COMMODITIES",db)
  commodities=db.query(Commodity).where(Commodity.simulation_id==simulation.id)
  for commodity in commodities:
      commodity.total_value=0
      commodity.total_price=0
      commodity.size=0
      db.add(commodity)
      cstocks=db.query(Stock).where(Stock.commodity_id==commodity.id)
      for cstock in cstocks:
          commodity.total_value+=cstock.value
          commodity.total_price+=cstock.price
          commodity.size+=cstock.size
  db.commit() # TODO is this necessary at this time?

  for commodity in commodities:
      if commodity.size>0:
        commodity.unit_price=commodity.total_price/commodity.size
        commodity.unit_value=commodity.total_price/commodity.size
        report(2,simulation.id,f"Setting the value of commodity {commodity.name} to {commodity.total_value} and its price to {commodity.total_price}",db)
        report(2,simulation.id,f"Setting the unit value of commodity {commodity.name} to {commodity.unit_value} and its unit price to {commodity.unit_price}",db)


def revalue_stocks(db:Session, simulation:Simulation):
  """ Interrogate all stocks.
  Set value from unit value and size of their commodity
  Set price from unit price and size of their commodity
  """
  report(1,simulation.id,"RESETTING PRICES AND VALUES",db)
  stocks=db.query(Stock).where(Stock.simulation_id==simulation.id)
  report(2,simulation.id,"Processing stocks",db)
  for stock in stocks:
      commodity=db.query(Commodity).where(Commodity.id == stock.commodity_id).first()
      db.add(stock)
      stock.value=stock.size*commodity.unit_value
      stock.price=stock.size*commodity.unit_price
      report(3,simulation.id,f"Setting the value of the stock [{stock.name}] to {stock.value} and its price to {stock.price}",db)

  db.commit()


def calculate_capital(db:Session, simulation:Simulation,industry:Industry)->float:
    """
    Calculate the initial capital of the given industry and return it
    This is equal to the sum of the prices of all its stocks
    Assumes that the price of all these stocks has been set
    """
    report(2,simulation.id,f"Calculating the capital of {industry.name}",db)
    result=0
    stocks=db.query(Stock).where(Stock.owner_type=="Industry"). filter (Stock.owner_id==industry.id)
    for stock in stocks:
        report(3,simulation.id,f"Stock [{stock.name}] of type {stock.owner_type} is adding {stock.price} to the capital of {industry.name}",db)
        result+=stock.price
    return result

def calculate_initial_capitals(db:Session, simulation:Simulation):
    """
    Calculate the initial capital of the given industry and return it
    This is equal to the sum of the prices of all its stocks
    Assumes that the price of all these stocks has been set correctly
    """
    report(1,simulation.id,f"CALCULATING INITIAL CAPITAL for simulation {simulation.id}",db)
    industries=db.query(Industry).where(Industry.simulation_id==simulation.id)
    for industry in industries:
      report(2,simulation.id,f"Asking for the capital of {industry.name}",db)      
      db.add(industry)
      industry.initial_capital=calculate_capital(db,simulation,industry)
    db.commit()

def calculate_current_capitals(db:Session, simulation:Simulation):
    """
    Calculate the current capital of all industries in the simulation.
    Set the profit and the profit rate of each industry.
    Assumes that the price of all stocks has been set correctly.
    """
    report(1,simulation.id,"CALCULATING CURRENT CAPITAL",db)
    industries=db.query(Industry).where(Industry.simulation_id==simulation.id)
    for industry in industries:
      db.add(industry)
      industry.current_capital=calculate_capital(db,simulation,industry)
      industry.profit=industry.current_capital-industry.initial_capital
      industry.profit_rate=industry.profit/industry.initial_capital
    db.commit()


