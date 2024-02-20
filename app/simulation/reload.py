from sqlalchemy.orm import Session
import json
from sqlalchemy import insert
from ..models import Buyer, Seller, Stock
from .demand import report


def reload_table(session: Session, baseModel, filename: str, reload: bool, simulation_id:int):
    report(1,simulation_id,f"Initialising database with file {filename}", session)
    query = session.query(baseModel)
    query.delete(synchronize_session=False)
    if reload:
        file = open(filename)
        jason = json.load(file)
        for item in jason:
            new_object = baseModel(**item)
            session.add(new_object)
    session.commit()

def initialise_buyers_and_sellers(session, simulation_id):
    report(2, simulation_id, "Creating a list of sellers", session)
    query = session.query(Seller)
    query.delete(synchronize_session=False)
    stock_query = session.query(Stock).where(
        Stock.simulation_id == simulation_id, Stock.usage_type == "Sales"
    )
    for stock in stock_query:
        owner = stock.owner(session)
        commodity = stock.commodity(session)
        money_stock_id = owner.money_stock(session).id
        sales_stock_id = stock.id
        owner_type = stock.owner_type
        commodity_id = commodity.id
        report(
            3,
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

    report(2, simulation_id, "Creating a list of buyers", session)
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
            3,
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

