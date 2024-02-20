from sqlalchemy.orm import Session
import json
from sqlalchemy import insert
from ..models import Buyer, Seller, Stock 
from .demand import report

def reload_table(db: Session, baseModel, filename: str, reload: bool, simulation_id:int):
    """
    Initialise one table,specified by baseModel, from JSON fixture data specified by filename.

    Sets the username of this table to be the admin user.

    TODO something more robust is required.
    """
    report(2,simulation_id,f"Initialising table {filename}", db)
    query = db.query(baseModel)
    query.delete(synchronize_session=False)
    if reload:
        file = open(filename)
        jason = json.load(file)
        for item in jason:
            new_object = baseModel(**item)
            new_object.username="admin" 
            db.add(new_object)
    db.commit()

def initialise_buyers_and_sellers(session, simulation_id):
    """
    Create a helper table of buyers and sellers.

    Used by 'Trade' action, to organise the allocation of demand to supply
    and to conduct the actual transfers of goods and money from one owner to another.

    The objects in this table are not cloned. They are references to the original objects
    in the underlying owner and stock tables.

    So when trade actually takes place, using these two tables, the result modifies
    the original objects, not copies of them.
    """
    report(1, simulation_id, "Creating a list of sellers for simulation {simulation_id}", session)
    query = session.query(Seller)
    query.delete(synchronize_session=False)
    stock_query = session.query(Stock).where(
        Stock.simulation_id == simulation_id, Stock.usage_type == "Sales"
    )
    for stock in stock_query:
        owner = stock.owner(session)
        print(f"Processing the owner {owner.name} with id {owner.id}")
        commodity = stock.commodity(session)
        money_stock_id = owner.money_stock(session).id
        sales_stock_id = stock.id
        owner_type = stock.owner_type
        commodity_id = commodity.id
        report(
            2,
            simulation_id,
            f"Adding seller {owner.name} type {owner_type} selling {stock.name} ({commodity.name})for money {money_stock_id}",
            session,
        )
        seller = {
            "simulation_id": simulation_id,
            "owner_type": owner_type,
            "sales_stock_id": sales_stock_id,
            "money_stock_id": money_stock_id,
            "commodity_id": commodity_id,
        }
        new_seller = Seller(**seller)
        session.add(new_seller)
    session.commit()

    report(1, simulation_id, "Creating a list of buyers", session)
    query = session.query(Buyer)
    query.delete(synchronize_session=False)
    stock_query = session.query(Stock).where(
        Stock.simulation_id == simulation_id,
        Stock.usage_type != "Money",
        Stock.usage_type != "Sales",
    )
    for stock in stock_query:
        owner = stock.owner(session)
        commodity = stock.commodity(session)
        money_stock_id = owner.money_stock(session).id
        purchase_stock_id = stock.id
        owner_type = stock.owner_type
        commodity_id = commodity.id
        report(
            2,
            simulation_id,
            f"Adding buyer {owner.name} type {owner_type} buying {stock.name} ({commodity.name}) using money {money_stock_id}",
            session,
        )
        buyer = {
            "simulation_id": simulation_id,
            "owner_type": owner_type,
            "purchase_stock_id": purchase_stock_id,
            "money_stock_id": money_stock_id,
            "commodity_id": commodity_id,
        }
        new_buyer = Buyer(**buyer)
        session.add(new_buyer)
    session.commit()

