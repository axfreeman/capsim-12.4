from ..models import Simulation, Industry, Industry_stock
from .demand import report
from sqlalchemy.orm import Session

def produce(session:Session, simulation:Simulation):
    """Tell all industries to produce."""

    report(1, simulation.id, "PRODUCTION", session)
    iquery = session.query(Industry).where(Industry.simulation_id == simulation.id)

    for ind in iquery:
        industry_produce(ind, session, simulation)

def industry_produce(industry:Industry, db:Session, simulation:Simulation)->str:
    """Tell  the given industry to produce.

    Increase the size of self.sales_stock by self.output_scale.
    
    Calculate the amount of each productive Stock that is used up and
    decrease its size by that amount.

    Calculate the value of each industrially-produced productive Stock that
    is used up and add this to the value of self.sales_stock.

    Add the used-up size of each socially-produced productive Stock to 
    the value of self.sales_stock.
    """

    report(2, simulation.id, f"{industry.name} is producing", db)
    sales_stock = industry.sales_stock(db)
    db.add(sales_stock)
    sc = sales_stock.commodity(db)
    report(3,simulation.id,
        f"{sales_stock.name} of {sc.name} before production is {sales_stock.size} with value {sales_stock.value}",db,
    )

    productive_stocks_query = db.query(Industry_stock).filter(
        Industry_stock.simulation_id == simulation.id,
        Industry_stock.industry_id == industry.id,
        Industry_stock.usage_type == "Production",
    )
    for stock in productive_stocks_query:
        db.add(stock)
        commodity = stock.commodity(db)
        report(4,simulation.id,
            f"Processing '{stock.name}' with size {stock.size}, value {stock.value} and unit value {sc.unit_value}",db,
        )

        # Evaluate the size and value contribution of this stock
        if commodity.name == "Labour Power":
            # Labour Power adds its magnitude, not its value
            value_contribution=stock.flow_per_period(db)
            stock.size -= value_contribution
            stock.value-=value_contribution*commodity.unit_value
            stock.price-= value_contribution*commodity.unit_price
            report(4, simulation.id, f"Labour Power adds {value_contribution} and its size becomes {stock.size}", db)
        else:
            value_contribution = stock.flow_per_period(db)* sc.unit_value
            # Other productive stocks transfer their value, not their magnitude
            stock.value -= value_contribution
            stock.size -=stock.flow_per_period(db)
            stock.price-= stock.flow_per_period(db)*commodity.unit_price
            report(4,simulation.id,
                f"{stock.name} transfers value {value_contribution} at unit value {commodity.unit_value} and its size becomes {stock.size}",db,
            )

        sales_stock.value += value_contribution
        sales_stock.size = industry.output_scale/simulation.periods_per_year
        report(4, simulation.id, f"Sales value rises to {sales_stock.value}", db)
    # TODO If MELT is not 1, we have to account below for the value of money
    sales_stock.price=sales_stock.value
    report(
        3, simulation.id, f"Sales value has now become {sales_stock.value}", db
    )
    db.commit()

