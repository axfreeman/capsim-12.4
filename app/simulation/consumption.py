from sqlalchemy.orm import Session
from ..models import SocialClass, Simulation, Class_stock
from .demand import report

"""This module contains functions needed to implement the consumption action.
"""

def consume(db:Session, simulation:Simulation)->str:
    """Tell all classes to consume and reproduce their product if they have one.
    TODO currentluy there are no population dynamics
    """

    report(1,simulation.id,f"CONSUMPTION AND REPRODUCTION",db,)

    squery = db.query(SocialClass).where(
        SocialClass.simulation_id == simulation.id
    )

    for social_class in squery:
        class_consume(social_class, db, simulation)

    return "Consumption complete"

def class_consume(social_class:SocialClass, db:Session, simulation:Simulation):
    """Tell one social class to consume and reproduce its product if it has one.
    No population dynamics at present - just consumption.
    """
    report(2,simulation.id,
        f"Social Class {social_class.name} is reproducing itself",db,
    )

    ss = social_class.sales_stock(db)
    db.add(ss)

    report(2,simulation.id,
        f"Sales stock size before consumption is {ss.size} with value {ss.value}",db,
    )

    consuming_stocks_query = db.query(Class_stock).where(
        Class_stock.simulation_id == simulation.id,
        Class_stock.class_id == social_class.id,
        Class_stock.usage_type == "Consumption",
    )

    for stock in consuming_stocks_query:
        db.add(stock)
        commodity=stock.commodity(db)
        report(3,simulation.id,
            f"Consuming stock of {stock.name} of usage type {stock.usage_type} whose size is {stock.size}",db,
        )
        stock.size -=stock.flow_per_period(db)  # eat according to defined consumption standards
        stock.price-=stock.flow_per_period(db)*commodity.unit_price
        stock.value-=stock.flow_per_period(db)*commodity.unit_value
    report(3,simulation.id,
        f"Replenishing the sales stock of {social_class.name} with a population of {social_class.population}",db,
    )
    
    # Currently no population dynamics and no differential labour intensity
    # Capitalists are assumed here (as per Cheng et al.) to supply services
    # in proportion to their number. But in neoclassical theory they would
    # have to supply in proportion to their capital. Others who believe this
    # nonsense will have to construct algorithms instantiating it if they
    # wish to test it logically.
    ss.size = (
        social_class.population
    )

    report(3,simulation.id,
        f"Supply of {ss.name} has reached {ss.size}",db,
    )
    db.commit()
