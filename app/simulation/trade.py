"""This module contains functions used in handling the trade action
"""

from ..models import Buyer, Seller, Stock, Commodity
from .demand import report

def constrain_demand(session,simulation):
    """Constrain demand to supply.
    TODO mostly untested
    """
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

def buy_and_sell(db, simulation):
    """Implements buying and selling.

    Uses two helper classes 'Buyer' and 'Seller' which are created when the
    simulation is initialized. 
    
    An instantiation of each classes is stored in the database.

    It does not change once initialised.

    It contains pointers to the underlying Owner objects, on which this
    function operates.

    TODO if demand is actually less than supply then we need some mechanism to oblige sellers to sell less.
    This can probably done within this function - as indeed may be possible for the allocation of demand itself.
    """

    report(1, simulation.id, f"Starting trade with simulation {simulation.id}", db)
    for seller in db.query(Seller).where(Seller.simulation_id == simulation.id):
        sales_stock = seller.sales_stock(db)
        report(2,simulation.id,
            f"seller {seller.owner_name(db)} can sell {sales_stock.size} of its stock and is looking for buyers {sales_stock.name}",db,
        )

        for buyer in db.query(Buyer).where(
            Buyer.simulation_id == simulation.id,
            Buyer.commodity_id == seller.commodity_id,
        ):
            report(3,simulation.id,
                f"buyer {buyer.owner_name(db)} is buying {buyer.purchase_stock(db).demand}",db,
            )
            buy(buyer, seller, simulation, db)
    db.commit()

def buy(buyer, seller, simulation, db):
    """
    Tell seller to sell whatever the buyer demands and collect the money.
    
    Do not modify the value or price attributes of either stock here, because 
    they do not change when traded.
    """
    report(4,simulation.id,
        f"buyer {buyer.owner_name(db)} is buying {buyer.purchase_stock(db).demand}",db,
    )
    bp = buyer.purchase_stock(db)
    sp = seller.sales_stock(db)
    db.add(bp)
    db.add(sp)
    bms = buyer.money_stock(db)
    sms = seller.money_stock(db)
    db.add(bms)
    db.add(sms)
    commodity = seller.commodity(db)  # does not change yet, so no need to add it to the session
    unitPrice = commodity.unit_price
    unitValue = commodity.unit_value
    amount = bp.demand
    report(4,simulation.id,
        f"Buying {amount} at price {unitPrice} and value {unitValue}",db,
    )
    bp.size += amount
    bp.price=bp.size*unitPrice
    bp.value=bp.size*unitValue
    bp.demand -= amount
    sp.size -= amount
    sp.value=sp.size*unitValue
    sp.price=sp.size*unitPrice
    if bms.id == sms.id:  # Internal trade to the sector
        report(4,simulation.id,
            "Money stocks are the same so no transfer effected",db,
        )
    else:
        # TODO account for MELT. Money can have a value different from its price
        sms.size += amount * unitPrice
        sms.value=sms.size
        sms.price=sms.size
        bms.size -= amount * unitPrice
        bms.value=bms.size
        bms.price=bms.size
    db.commit()

