from ..models import Buyer, Seller, Stock, Commodity, Industry, SocialClass, Simulation
from .demand import report


def production(session, simulation):
    report(1, simulation.id, "PRODUCTION", session)
    iquery = session.query(Industry).where(Industry.simulation_id == simulation.id)
    squery = session.query(SocialClass).where(
        SocialClass.simulation_id == simulation.id
    )

    for ind in iquery:
        industry_produce(ind, session, simulation)
    for social_class in squery:
        social_class_reproduce(social_class, session, simulation)


# tell one industry to produce
def industry_produce(industry, session, simulation):
    report(2, simulation.id, f"{industry.name} is producing", session)
    sales_stock = industry.sales_stock(session)
    session.add(sales_stock)
    sc = sales_stock.commodity(session)
    report(
        3,
        simulation.id,
        f"{sales_stock.name} of {sc.name} before production is {sales_stock.size} with value {sales_stock.value}",
        session,
    )
    productive_stocks_query = session.query(Stock).where(
        Stock.simulation_id == simulation.id,
        Stock.owner_id == industry.id,
        Stock.usage_type == "Production",
    )
    for stock in productive_stocks_query:
        session.add(stock)
        commodity = stock.commodity(session)
        report(
            4,
            simulation.id,
            f"Processing '{stock.name}' with size {stock.size}, value {stock.value} and unit value {sc.unit_value}",
            session,
        )
        # Use up the stock required to produce
        if commodity.name == "Labour Power":
            v = (
                stock.size  # Labour Power adds its magnitude, not its value
            )  # TODO modify this if production is constrained by allowable output scale
            stock.size -= v
            report(4, simulation.id, f"Labour Power adds it size {v}", session)
        else:
            v = (
                stock.size * sc.unit_value
            )  # Capital transfers its value, not its magnitude
            if v != stock.value:
                report(
                    4,
                    simulation.id,
                    f"Discrepancy in stock value which is {stock.value} and should be {v}",
                    session,
                )
                # TODO the value should already have been calculated
            stock.value = 0  # TODO modify this if production is constrained by allowable output scale
            stock.size = 0  # TODO modify this if production is constrained by allowable output scale
            report(
                4,
                simulation.id,
                f"{stock.name} transfers value {v} at unit value {sc.unit_value} and its size becomes {stock.size}",
                session,
            )

        sales_stock.value += v
        sales_stock.size = industry.output_scale
        report(3, simulation.id, f"Sales value becomes {sales_stock.value}", session)
    report(
        3, simulation.id, f"Sales value is being set to {sales_stock.value}", session
    )
    session.commit()


# tell one social class to reproduce
# no population dynamics at present - just consumption
def social_class_reproduce(sc, session, simulation):
    report(
        2,
        simulation.id,
        f"Social Class {sc.name} is reproducing itself",
        session,
    )
    ss = sc.sales_stock(session)
    session.add(ss)

    report(
        2,
        simulation.id,
        f"Sales stock size before production is {ss.size} with value {ss.value}",
        session,
    )
    consuming_stocks_query = session.query(Stock).where(
        Stock.simulation_id == simulation.id,
        Stock.owner_id == sc.id,
        Stock.usage_type == "Consumption",
    )

    for stock in consuming_stocks_query:
        session.add(stock)
        report(
            3,
            simulation.id,
            f"Consuming stock of {stock.name} of usage type {stock.usage_type} whose size is {stock.size}",
            session,
        )
        stock.size = 0  # eat everything available

    # Consumption has no effect on supply of what classes sell
    # TODO but if there are population dynamics, this will change
    report(
        3,
        simulation.id,
        f"Replenishing the sales stock of {sc.name} with a population of {sc.population}",
        session,
    )
    ss.size = (
        sc.population
    )  # TODO different classes may consume different proportions. This was the original purpose of the field 'requirement' which should be reinstated
    report(
        3,
        simulation.id,
        f"Supply of {ss.name} has reached {ss.size}",
        session,
    )
    session.commit()
