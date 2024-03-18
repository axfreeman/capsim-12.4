from fastapi import Depends, Query, Depends
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from .database import Base
from sqlalchemy.orm import relationship, Session

"""This module contains models, and their methods, for the objects of
the system, except for the User model which is in authorization.py.
"""

class Simulation(Base):
    """
    Simulation is the primary model of the projet. Each entry in the
    Simulation database defines the state of the simulation at a
    single point in (virtual) time defined by time_stamp.

    A User can run a number of simulations concurrently and switch
    between them. Using the user-dashboard, users can also create,
    delete and switch between Simulations, but must choose from
    one of a number of predefined Templates. Future versions of the
    project will permit users to define and edit Templates but this
    requires a lot of validation logic.

    Every object of the simulation (Commodity, Industry, Stock, etc)
    belongs to one simulation and has a foreign key that links to it
    """

    __tablename__ = "simulations"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    time_stamp = Column(Integer)
    username = Column(String, nullable=True)  # Foreign key to the User model
    state = Column(String)  # what stage the simulation has reached
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
    # TODO not sure if this is used any more
    owner = relationship("User")  # See part 77 of the tutorial. Not used at present

class Commodity(Base):
    """
    The commodity object refers to a type of tradeable good, for example
    Means of Production, Means of Consumption, Labour Power. In Marx's
    terms it is a 'use value'. Each commodity has a one-many relation
    to the stocks in the simulation, so if an industry owns a stock of
    Means of Production, the stock object will have a foreign key to
    the Means of Production Commodity.

    The simulation keeps track of aggregate magnitudes associated with
    each Commodity, such as its total price, total value, total quantity
    and so on.

    It also keeps track of the total supply of, and the total demand for
    that Commodity.
    """

    __tablename__ = "commodities"
    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    username = Column(String, nullable=True)
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
    """Each Industry is a basic productive unit.

    It owns:
     several Productive Stocks;
     a SalesStock;
     a MoneyStock;

    These Stocks have a foreign key uniquely stating which Industry they
    belong to.

    During the 'produce' action, Industries are asked to produce output
    on a scale given by output_scale.

    To this end, they use up the Productive Stocks.

    The amount of each such Stock which is consumed in this way depends on
    Industry.output_scale, Stock.requirement, and Commodity.turnover_time
    where Commodity is referenced by Stock.commodity_id.

    During the 'trade' action, Industries buy the Stocks they need, and
    sell their SalesStock. They may or may not manage to get all the
    productive Stocks they need. If they fail, output_scale is reduced.

    To facilitate the calculation, the app calculates the money cost of
    buying the productive Stocks needed for one unit of output in one
    period.

    This is provided by the method 'self.unit_cost'.
    """

    __tablename__ = "industries"

    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    username = Column(String, nullable=True)
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

    def unit_cost(self, db: Session):
        """Calculate the cost of producing a single unit of output."""
        cost = 0
        for stock in (
            db.query(Stock)
            .where(Stock.owner_id == self.id)
            .where(Stock.usage_type == "Production")
        ):
            print(
                f"Stock called {stock.name} is adding {stock.unit_cost(db)} to its industry's unit cost"
            )
            cost += stock.unit_cost(db)
        return cost

    def simulation(self, db: Session):
        """
        Helper method yields the (unique) Simulation this industry belongs to.
        """
        return db.get_one(Simulation, self.simulation_id)

    def sales_stock(self, db: Session):
        """Helper method yields the Sales Stock of this industry."""
        result = get_industry_sales_stock(
            self, db
        )  # workaround because pydantic won't easily accept this query in a built-in function
        if result == None:
            raise Exception(
                f"INDUSTRY {self.name} with id {self.id} and simulation id {self.simulation_id} HAS NO SALES STOCK"
            )
        return result

    def money_stock(self, session):
        """Helper method yields the Money Stock of this industry."""
        return get_industry_money_stock(
            self, session
        )  # workaround because pydantic won't easily accept this query in a built-in function

def get_industry_sales_stock(industry, session):
    """Workaround because pydantic won't accept this query in a built-in function."""
    return (
        session.query(Stock)
        .filter(
            Stock.owner_id == industry.id,
            Stock.usage_type == "Sales",
            Stock.owner_type == "Industry",
            Stock.simulation_id == industry.simulation_id,
        )
        .first()
    )

def get_industry_money_stock(industry, session):
    """workaround because pydantic won't accept this query in a built-in function."""
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
    username = Column(String, nullable=True)
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
    """Stocks are the things that are produced, consumed, and traded in a
    market economy.

    A Stock knows:
        which Commodity it consists of (in Marx's terms, its Use Value);
        who owns it (which may either be an Industry or a Class);
        which Simulation it belongs to;
        quantitative information notably its size, value and price.
    Every Stock has a usage_type which may be Consumption, Production or Money.
    This is a substitute for subclassing, since these are all types of Stock.

    The other fields depend to some extent on the usage_type.

    Thus a productive Stock has a field Stock.requirement which says how
    much of it will be used for its Industry to produce Industry.output_scale.

    The helper method Stock.unit_cost says how much it will cost to do this.

    (TODO document the properties of Consumption Stocks)
    """

    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, nullable=False)
    # We cannot make this a foreign key because the owner can either be
    # a social class or an industry and we don't know which.
    # This arises from the difficulty of implementing polymorphic relations in an SQL database
    owner_id = Column(Integer, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    username = Column(String, nullable=True)
    commodity_id = Column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)  # Owner.Name+Commodity.Name+usage_type
    owner_type = Column(String)  #'Industry' or 'Class'
    usage_type = Column(String)  # 'Consumption' or 'Production'
    size = Column(Float)
    value = Column(Float)
    price = Column(Float)
    requirement = Column(Float)
    demand = Column(Float)

    def flow_rate(self, db: Session) -> float:
        """The annual rate at which this Stock is consumed.

        Applies only to productive stocks and consumption stocks.

        Returns zero for Money and Sales Stocks.
        """
        if self.usage_type == "Production":
            industry = db.query(Industry).where(Industry.id == self.owner_id).first()
            return industry.output_scale * self.requirement
        elif self.usage_type == "Consumption":
            social_class = (
                db.query(SocialClass).where(SocialClass.id == self.owner_id).first()
            )
            return social_class.population * social_class.consumption_ratio
        else:
            return 0.0

    def flow_per_period(self, db: Session) -> float:
        """The same as flow_rate, but per period instead of per year."""
        simulation = (
            db.query(Simulation).where(Simulation.id == self.simulation_id).first()
        )
        return self.flow_rate(db) / simulation.periods_per_year

    def standard_stock(self, db: Session) -> float:
        """The normal stock which an owner must maintain in order to conduct
        production or consumption.

        Applies only to productive stocks and consumption stocks.

        Returns zero for Money and Sales Stocks.
        """
        if self.usage_type == "Production":
            commodity = (
                db.query(Commodity).where(Commodity.id == self.commodity_id).first()
            )
            return self.flow_rate(db) * commodity.turnover_time
        elif self.usage_type == "Consumption":
            commodity = (
                db.query(Commodity).where(Commodity.id == self.commodity_id).first()
            )
            # Not sure about this one. I guess even food has a turnover time.
            # But makes sense for consumer durables and housing, so quite a large
            # proportion of consumer spending.
            return self.flow_rate(db) * commodity.turnover_time
        else:
            return 0.0

    def owner(self, db: Session):
        """Returns either an Industry or a SocialClass, depending on
        self.usage_type.

        This is a substitute for subclassing, which I find too complex
        to store in a database polymorphically (that is, taking due
        account of subclassing).
        """
        if self.owner_type == "Industry":
            return db.get_one(Industry, self.owner_id)
        elif self.owner_type == "Class":
            return db.get_one(SocialClass, self.owner_id)
        else:
            print(f"owner type for stock with id {self.id} was not understood")

    def commodity(self, db: Session):
        return db.get_one(Commodity, self.commodity_id)

    def simulation(self, session):
        return session.get_one(Simulation, self.simulation_id)

    def unit_cost(self, db: Session):
        """Money price of using this Stock to make one unit of output
        in a period.

        Returns zero if Stock is not productive, which is harmless -
        nevertheless, caller should invoke this method only on productive
        Stocks.
        """
        return self.requirement * self.commodity(db).unit_price

class Industry_stock(Base):
    """Stocks are produced, consumed, and traded in a
    market economy.

    There are two types of stock:
        Those that belong to Industries
        Those that belong to Classes

    An Industry_stock knows:
        which Simulation it belongs to;
        which Commodity it consists of (in Marx's terms, its Use Value);
        quantitative information notably its size, value and price;
        which Industry it belongs to.

    It has a usage_type which may be Consumption, Production or Money.
    Note that an industry can own any of these.
    This is because Consumption goods are produced by industries.

    Usage type is a substitute for subclassing.

    The field 'requirement' says how much of it will be used for its
    Industry to produce a unit of output.

    The helper method Stock.unit_cost says how much it will cost to do this.

    """

    __tablename__ = "industry_stocks"
    id = Column(Integer, primary_key=True, nullable=False)
    industry_id = Column(Integer, ForeignKey("industries.id"), nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    commodity_id = Column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)  # Owner.Name+Commodity.Name+usage_type
    usage_type = Column(String)  # 'Consumption', 'Production' or 'Money'
    size = Column(Float)
    value = Column(Float)
    price = Column(Float)
    requirement = Column(Float)
    demand = Column(Float)

class Class_stock(Base):
    """Stocks are produced, consumed, and traded in a
    market economy.

    There are two types of stock:
        Those that belong to Industries
        Those that belong to Classes

    A Class_stock knows:
        which Simulation it belongs to;
        which Commodity it consists of (in Marx's terms, its Use Value);
        quantitative information notably its size, value and price;
        which Social Class it belongs to.

    It has a usage_type which may be Consumption, Production or Money.
    Note that classes can own any type of stock.
    This is because Labour Power is a stock of type Production.

    Usage_type is a substitute for subclassing, since these are all types of Stock.

    """

    __tablename__ = "class_stocks"
    id = Column(Integer, primary_key=True, nullable=False)
    class_id = Column(Integer, ForeignKey("social_classes.id"), nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    commodity_id = Column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)  # Owner.Name+Commodity.Name+usage_type
    usage_type = Column(String)  # 'Consumption', Production' or 'Money'
    size = Column(Float)
    value = Column(Float)
    price = Column(Float)
    demand = Column(Float)

class Trace(Base):
    """
    Trace reports the progress of the simulation in a format meaningful
    for the user. It works in combination with logging.report(). A call
    to report() creates a single trace entry in the database and prints
    it on the console
    """

    __tablename__ = "trace"
    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(Integer)
    time_stamp = Column(Integer)
    username = Column(String, nullable=True)
    level = Column(Integer)
    message = Column(String)

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
