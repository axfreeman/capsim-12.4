from fastapi import Depends, Query
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from .database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_superuser = Column(Boolean, nullable=False, default=False)


# The below, which work with postgres, don't work with sqlite
# But since we aim to get this working in production with postgres, we haven't fixed it
# date_joined = Column(
#     TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
# )
# last_login = Column(
#     TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
# )


class Trace(Base):
    __tablename__ = "trace"
    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(Integer)
    time_stamp = Column(Integer)
    level = Column(Integer)
    message = Column(String)


class Simulation(Base):
    __tablename__ = "simulations"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    time_stamp = Column(Integer)
    state = Column(String)
    periods_per_year = Column(Float)
    population_growth_rate = Column(Float)
    investment_ratio = Column(Float)
    labour_supply_response = Column(String)
    price_response_type = Column(String)
    melt_response_type = Column(String)
    currency_symbol = Column(String)
    quantity_symbol = Column(String)
    melt = Column(Float)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner = relationship("User")  # See part 77


# TODO change name of table to match name of model
class Commodity(Base):
    __tablename__ = "commodities"
    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)
    origin = Column(String)
    usage = Column(String)
    size = Column(Float)
    total_value = Column(Float)
    total_price = Column(Float)
    unit_value = Column(Float)
    unit_price = Column(Float)
    turnover_time = Column(Float)
    demand = Column(Float)
    supply = Column(Float)
    allocation_ratio = Column(Float)
    display_order = Column(Integer)
    image_name = Column(String)
    tooltip = Column(String)
    monetarily_effective_demand = Column(Float)
    investment_proportion = Column(Float)
    successor_id = Column(Integer, nullable=True)  # Helper column to use when cloning

    simulation_name = relationship("Simulation")


class Industry(Base):
    __tablename__ = "industries"

    # id = Column(Integer, Sequence('industry_seq', start=10001, increment=1), primary_key=True, nullable=False)
    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)
    output = Column(String)
    output_scale = Column(Float)
    output_growth_rate = Column(Float)
    initial_capital = Column(Float)
    work_in_progress = Column(Float)
    current_capital = Column(Float)
    profit = Column(Float)
    profit_rate = Column(Float)
    successor_id = Column(Integer, nullable=True)  # Helper column to use when cloning

    def simulation(self, session):
        return session.get_one(Simulation, self.simulation_id)

    def sales_stock(self, session):
        industry=self
        # print(f"Asking for the sales stock for industry {industry.name} with id {industry.id} and simulation id {industry.simulation_id}")
        result= get_industry_sales_stock(self, session)
        if result==None:
            raise Exception(f"INDUSTRY {self.name} with id {self.id} and simulation id {self.simulation_id} HAS NO SALES STOCK")
        return result

    def money_stock(self, session):
        return get_industry_money_stock(self, session)


# workaround because pydantic won't easily accept this query in a built-in function
def get_industry_sales_stock(industry, session):
    # print(f"Looking for the sales stock for industry {industry.name} with id {industry.id} and simulation id {industry.simulation_id}")
    # query=session.query(Stock).filter(
    #         # Stock.owner_id == industry.id,
    #         # Stock.usage_type == "Sales",
    #         # Stock.owner_type == "Industry",
    #         Stock.simulation_id == industry.simulation_id)
    # for row in query:
    #     print("Row in the query is", row)

    return session.query(Stock).filter(
            Stock.owner_id == industry.id,
            Stock.usage_type == "Sales",
            Stock.owner_type == "Industry",
            Stock.simulation_id == industry.simulation_id,
        ).first()

def get_industry_money_stock(industry, session):
    return (
        session.query(Stock)
        .filter(
            Stock.owner_id == industry.id,
            Stock.usage_type == "Money",
            Stock.owner_type == "Industry",
            Stock.simulation_id == industry.simulation_id,
        )
        .first()
    )


class SocialClass(Base):
    __tablename__ = "social_classes"

    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)
    population = Column(Float)
    participation_ratio = Column(Float)
    consumption_ratio = Column(Float)
    revenue = Column(Float)
    assets = Column(Float)
    successor_id = Column(Integer, nullable=True)  # Helper column to use when cloning

    def simulation(self, session):
        return session.get_one(Simulation, self.simulation_id)

    def sales_stock(self, session):
        return get_class_sales_stock(self, session)

    def money_stock(self, session):
        return get_class_money_stock(self, session)


def get_class_sales_stock(social_class, session):
    return (
        session.query(Stock)
        .filter(
            Stock.owner_id == social_class.id,
            Stock.usage_type == "Sales",
            Stock.owner_type == "Class",
            Stock.simulation_id == social_class.simulation_id,
        )
        .first()
    )


def get_class_money_stock(social_class, session):
    return (
        session.query(Stock)
        .filter(
            Stock.owner_id == social_class.id,
            Stock.usage_type == "Money",
            Stock.owner_type == "Class",
            Stock.simulation_id == social_class.simulation_id,
        )
        .first()
    )


class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, nullable=False)
    owner_id = Column(Integer, nullable=False)
    simulation_id = Column(Integer, nullable=False)
    commodity_id = Column(Integer, nullable=False)
    name = Column(String)  # Owner.Name+Commodity.Name+usage_type
    owner_type = Column(String)  #'Industry' or 'Class'
    usage_type = Column(String)  # 'Consumption' or 'Production'
    size = Column(Float)
    value = Column(Float)
    price = Column(Float)
    requirement = Column(Float)
    demand = Column(Float)

    def owner(self, session):
        if self.owner_type == "Industry":
            return session.get_one(Industry, self.owner_id)
        elif self.owner_type == "Class":
            return session.get_one(SocialClass, self.owner_id)
        else:
            print(f"owner type for stock with id {self.id} was not understood")

    def commodity(self, session):
        return session.get_one(Commodity, self.commodity_id)

    def simulation(self, session):
        return session.get_one(Simulation, self.simulation_id)


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(Integer)
    owner_type = Column(String)  # `Industry` or `Class`
    purchase_stock_id = Column(Integer)
    money_stock_id = Column(Integer)
    commodity_id = Column(Integer)

    def simulation(self, session):
        return session.get_one(Simulation, self.simulation_id)

    def purchase_stock(self, session):
        return session.get_one(Stock, self.purchase_stock_id)

    def money_stock(self, session):
        return session.get_one(Stock, self.money_stock_id)

    def commodity(self, session):
        return session.get_one(Commodity, self.commodity_id)

    def owner_name(self, session):  # Really just for diagnostic purposes only
        if self.owner_type == "Industry":
            return session.get_one(Industry, self.purchase_stock(session).owner_id).name
        else:
            return session.get_one(
                SocialClass, self.purchase_stock(session).owner_id
            ).name


class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(Integer)
    owner_type = Column(String)  # `Industry` or `Class`
    sales_stock_id = Column(Integer)
    money_stock_id = Column(Integer)
    commodity_id = Column(Integer)

    def simulation(self, session):
        return session.get_one(Simulation, self.simulation_id)

    def sales_stock(self, session):
        return session.get_one(Stock, self.sales_stock_id)

    def money_stock(self, session):
        return session.get_one(Stock, self.money_stock_id)

    def commodity(self, session):
        return session.get_one(Commodity, self.commodity_id)

    def owner_name(self, session):  # Really just for diagnostic purposes only
        if self.owner_type == "Industry":
            return session.get_one(Industry, self.sales_stock(session).owner_id).name
        else:
            return session.get_one(SocialClass, self.sales_stock(session).owner_id).name

    def owner_id(self, session):  # also just for diagnostic purposes
        if self.owner_type == "Industry":
            return session.get_one(Industry, self.sales_stock(session).owner_id).id
        else:
            return session.get_one(SocialClass, self.sales_stock(session).owner_id).id


class SocialStocks(Base):
    __tablename__ = "social_stocks"
    id = Column(Integer, primary_key=True, nullable=False)
    owner_id = Column(
        Integer, ForeignKey("social_classes.id", ondelete="CASCADE"), nullable=False
    )
    usage_type = Column(String)
    size = Column(Float)
    requirement = Column(Float)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    commodity_id = Column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False
    )
    demand = Column(Float)

    def owner(self, session):
        return session.get_one(SocialClass, self.owner_id)

    def commodity(self, session):
        return session.get_one(Commodity, self.commodity_id)


# Stocks owned by industries
class IndustryStocks(Base):
    __tablename__ = "industry_stocks"
    id = Column(Integer, primary_key=True, nullable=False)
    owner_id = Column(
        Integer, ForeignKey("industries.id", ondelete="CASCADE"), nullable=False
    )
    usage_type = Column(String)
    size = Column(Float)
    requirement = Column(Float)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    commodity_id = Column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False
    )
    demand = Column(Float)

    def owner(self, session):
        return session.get_one(Industry, self.owner_id)

    def commodity(self, session):
        return session.get_one(Commodity, self.commodity_id)
