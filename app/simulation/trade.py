from ..models import Buyer, Seller, Stock, Commodity
from .demand import report

# constrain demand to supply
def constrain_demand(session,simulation):
    report(1,simulation.id,"CONSTRAINING DEMAND TO SUPPLY",session)
    query=session.query(Commodity).where(Commodity.simulation_id==simulation.id)
    for commodity in query:
        session.add(commodity)
        if (commodity.usage=="PRODUCTIVE".strip()) or (commodity.usage=="CONSUMPTION".strip()):
            report(2,simulation.id,f'Demand for {commodity.name} is {commodity.demand} and supply is {commodity.supply}',session)
            if commodity.supply==0:
                report(3,simulation.id,f"Zero Supply of {commodity.name}",session)
                commodity.allocation_ratio=0
            elif commodity.demand<=commodity.supply:
                report(3,simulation.id,f'Supply exceeds or equals demand; no constraint applied',session)
                commodity.allocation_ratio=1
            else:
                # TODO untested
                report(3,simulation.id,f'Supply is less than demand; demand will be constrained',session)
                commodity.allocation_ratio=commodity.supply/commodity.demand
                commodity.demand*=commodity.allocation_ratio
                report(3,simulation.id,f'Demand for {commodity.name} has been constrained by supply to {commodity.demand}',session)
                report(3,simulation.id,f'Constraining stocks of {commodity.name} by a factor of {commodity.allocation_ratio}',session)

                stock_query=session.query(Stock).where(Stock.commodity_id==commodity.id)
                for stock in stock_query:
                    session.add(stock)
                    stock.demand=stock.demand*commodity.allocation_ratio
                    report(4,simulation.id, f"constraining stock {stock.id} demand to {stock.demand}",session)
    # TODO in 11.8 we now called set_commodities_from_stocks(simulation) but I don't see why


def buy_and_sell(session, simulation):
    # TODO if demand is actually less than supply then we need some mechanism to oblige sellers to sell less
    # This can probably done within this function - as indeed may be possible for the allocation of demand itself
    report(1, simulation.id, f"Starting trade with simulation {simulation.id}", session)
    for seller in session.query(Seller).where(Seller.simulation_id == simulation.id):
        sales_stock = seller.sales_stock(session)
        report(
            2,
            simulation.id,
            f"seller {seller.owner_name(session)} can sell {sales_stock.size} of its stock and is looking for buyers {sales_stock.name}",
            session,
        )

        for buyer in session.query(Buyer).where(
            Buyer.simulation_id == simulation.id,
            Buyer.commodity_id == seller.commodity_id,
        ):
            report(
                3,
                simulation.id,
                f"buyer {buyer.owner_name(session)} is buying {buyer.purchase_stock(session).demand}",
                session,
            )
            buy(buyer, seller, simulation, session)
    session.commit()
    set_commodities_from_stocks(simulation.id)

def buy(buyer, seller, simulation, session):
    report(
        4,
        simulation.id,
        f"buyer {buyer.owner_name(session)} is buying {buyer.purchase_stock(session).demand}",
        session,
    )
    bp = buyer.purchase_stock(session)
    sp = seller.sales_stock(session)
    session.add(bp)
    session.add(sp)
    bms = buyer.money_stock(session)
    sms = seller.money_stock(session)
    session.add(bms)
    session.add(sms)
    commodity = seller.commodity(
        session
    )  # does not change yet, so no need to add it to the session
    unitPrice = commodity.unit_price
    unitValue = commodity.unit_value
    amount = bp.demand
    report(
        4,
        simulation.id,
        f"Buying {amount} at price {unitPrice} and value {unitValue}",
        session,
    )
    bp.size += amount
    bp.demand -= amount
    sp.size -= amount
    if bms.id == sms.id:  # Internal trade to the sector
        report(
            4,
            simulation.id,
            "Money stocks are the same so no transfer effected",
            session,
        )
    else:
        sms.size += amount * unitPrice
        bms.size -= amount * unitPrice
    # we do not modify the value or price attributes of either stock here, because we recalculate prices and values separately, immediately after this step
    session.commit()


def set_commodities_from_stocks(simulation):
    pass
