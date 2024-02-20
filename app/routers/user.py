from fastapi import APIRouter, Depends
from typing import List
from app.authorization.auth import get_current_user_and_simulation, usPair, User
from app.database import get_db
from app.schemas import UserBase
from app.simulation.logging import report
from app.simulation.reload import initialise_buyers_and_sellers
from app.simulation.utils import calculate_current_capitals, calculate_initial_capitals, revalue_commodities, revalue_stocks
from ..models import Commodity, Industry, SocialClass, Stock, Simulation

from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/",response_model=List[UserBase])
def get_users(db: Session = Depends(get_db)):
    """Return all users.
    TODO should only be accessible to admin
    """
    users = db.query(User).all()
    return users

@router.get("/{username}",response_model=UserBase)
def get_user(username: str, db: Session = Depends(get_db)):
    """Return the user object for the user called username
    """
    user = db.query(User).filter(User.username == username).first()
    return user

def clone_model(model, session: Session, **kwargs):
    """
    Clone an arbitrary sqlalchemy model object without its primary key values
    These primary keys are then added by the caller
    Returns the clone unless the call is illegal (eg null model)
    Returns None if it can't be done
    """
    try:
        table = model.__table__
        non_pk_columns = [
            k for k in table.columns.keys() if k not in table.primary_key.columns.keys()
        ]
        data = {c: getattr(model, c) for c in non_pk_columns}
        data.update(kwargs)
        clone = model.__class__(**data)
        session.add(clone)
        session.commit()
        return clone
    except:
        return None


@router.get("/clone/{id}")
def create_simulation_from_template(
    id: str,
    db: Session = Depends(get_db),
    u:usPair = Depends(get_current_user_and_simulation),
):
    """
    Create a complete clone of the template defined by 'id'
    Rename the user to be the user who requested this clone
    """
    template = db.query(Simulation).filter(Simulation.id == int(id)).first()
    new_simulation = clone_model(template, db)
    if new_simulation is None:
        print("Illegal call to clone. Quitting without doing anything")
        return
    report(
        1,
        1,
        f"Create new simulation for {u.user.username} from template {template.name} with id {new_simulation.id}",
        db,
    )
    db.add(
        new_simulation
    )  # we commit twice, because we want to get the autogenerated id. There's probably a better way
    new_simulation.user_id = u.user.id
    new_simulation.username = u.user.username
    db.add(new_simulation)
    db.add(u.user)
    new_simulation.state = "DEMAND"  # The simulation starts at this point
    u.user.current_simulation = (
        new_simulation.id
    )  # when we create a new simulation, this is (initially) the current simulation
    db.commit()  # TODO reduce number of commits?

    # Clone all commodities in this simulation
    commodities = db.query(Commodity).filter(Commodity.simulation_id == template.id)
    for commodity in commodities:
        report(
            2,
            1,
            f"Cloning commodity {commodity.name}",
            db,
        )
        new_commodity = clone_model(commodity, db)
        db.add(
            new_commodity
        )  # we commit twice, because we want to get the autogenerated id. There's probably a better way
        db.add(
            commodity
        )  # seems to be transient after it is committed, which is a bit weird. So bring it out again, because we will modify it by adding successor_id
        new_commodity.simulation_id = new_simulation.id
        new_commodity.username = u.user.username
        commodity.successor_id = new_commodity.id
        db.commit()

    # Clone all industries in this simulation

    industries = db.query(Industry).filter(Industry.simulation_id == template.id)
    for industry in industries:
        report(
            2,
            1,
            f"Cloning industry {industry.name}",
            db,
        )
        new_industry = clone_model(industry, db)
        db.add(
            new_industry
        )  # we commit twice, because we want to get the autogenerated id. There's probably a better way
        db.add(
            industry  # seems to be transient after we committed it, which is a bit weird - so bring it out again, because we're going to modify it
        )
        new_industry.simulation_id = new_simulation.id
        new_industry.username = u.user.username
        industry.successor_id = new_industry.id
        db.commit()

    # Clone all classes in this simulation

    classes = db.query(SocialClass).filter(SocialClass.simulation_id == template.id)
    for socialClass in classes:
        report(
            2,
            1,
            f"Cloning class {socialClass.name}",
            db,
        )
        new_class = clone_model(socialClass, db)
        db.add(
            new_class
        )  # we commit twice, because we want to get the autogenerated id. There's probably a better way
        db.add(
            socialClass  # seems to be transient after we committed it, which is a bit weird - so bring it out again, because we're going to modify it
        )
        new_class.simulation_id = new_simulation.id
        new_class.username = u.user.username
        socialClass.successor_id = new_class.id
        db.commit()

    # Clone all stocks in this simulation

    stocks = db.query(Stock).filter(Stock.simulation_id == template.id)
    for stock in stocks:
        report(
            3,
            1,
            f"Cloning stock {stock.name} with id {stock.id}, owner id {stock.owner(db).id} , and commodity  {stock.commodity(db).name} [id {stock.commodity(db).id}]",
            db,
        )
        old_owner = stock.owner(db)
        old_commodity = stock.commodity(db)
        old_stock_owner_id = stock.owner_id
        successor_commodity_id = old_commodity.successor_id
        successor_id = old_owner.successor_id
        new_stock = clone_model(stock, db)
        db.add(
            new_stock
        )  # we commit twice, because we want to get the autogenerated id. There's probably a better way
        new_stock.simulation_id = new_simulation.id
        # This stock now has to be connected with its owner and commodity objects in the new simulation
        new_stock.owner_id = successor_id
        new_stock.username = u.user.username
        new_stock.commodity_id = successor_commodity_id
        new_stock.name = (
            new_stock.owner(db).name
            + "."
            + new_stock.commodity(db).name
            + "."
            + new_stock.usage_type
            + "."
            + str(new_stock.simulation_id)
        )
        db.commit()

    # Create buyers and sellers table
    initialise_buyers_and_sellers(db, new_simulation.id)
    revalue_commodities(db,new_simulation)
    revalue_stocks(db,new_simulation)
    calculate_initial_capitals(db,new_simulation)
    calculate_current_capitals(db,new_simulation)