from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import Session
from ..database import Base, get_db
from ..models import Simulation
from ..simulation.logging import report
from ..config import settings
from ..schemas import AuthDetails, Token
from ..reporting.caplog import logger

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3000

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},# TODO is this parameter necessary? Or even right?
)

class User(Base):
    """
    The user object contains everything needed to describe a user
    The Simulation object contains a foreign key pointing to the User.id field
    All other objects contain foreign keys pointing to the Simulation.id field

    The username and (hashed) password fields are used for logging in and out
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_superuser = Column(Boolean, nullable=False, default=False)
    is_logged_in = Column(Boolean, nullable=False, default=False)
    current_simulation = Column(Integer, nullable=False, default=0)

    def __init__(self, u, p):
        self.username = u
        self.password = pwd_context.hash(p)

class usPair:
    """
    Helper class for get_current_user() to serve a User and its
    Simulation together. 
    
    We tried to use tuples but fastAPI's Depends() did not allow it
    """
    user:User=None
    simulation:Simulation=0

    def __init__(self,user,simulation):
        self.user=user
        self.simulation=simulation

async def get_current_user_and_simulation(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> usPair:
    """
    Returns the currently logged-in user corresponding to the token in
    the request header, and the simulation this user is working on.

    Returns (None,None) and raises an exception if the user is not
    authenticated, or does not exist on the database

    Returns (User,None) if the user is OK but has no current simulation

    Cannot return (None, Simulation)
    """

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except Exception as error:
        logger.error(f"No meaningful token {token}. Client is probably not logged in")
        return usPair(None,None)
    if username is None:
        logger.error("Token contained no username. Client did not tell us anything meaningful")
        return usPair(None,None)
    user = get_user_from_username(username=username, db=db)
    if user is None:
        logger.error(f"Token was authenticated but {username} was not found in the database")
        return usPair(None,None)
    simulation = db.query(Simulation).where(Simulation.user_id == user.id).first()
    return usPair(user,simulation) # if there is no such simulation, this returns (user,None), as specified

def get_user_from_username(username: str, db: Session) -> User:
    """
    Looks up username in the database. 
    Returns the user if found, None if not
    """
    try:
        user = db.query(User).where(User.username == username).first()
    except Exception as error:
        logger.error(
            f"There was an error trying to find user {username}; the reason was {error}"
        )
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates an encoded jwt token from data.
    Usage is standard. Data contains the "SUB" key and the username
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_simulation(
    db: Session = Depends(get_db), u:usPair=Depends(get_current_user_and_simulation)
)->Simulation:
    """
    Synonym for get_current_user_and_simulation().simulation

    Since this is a synonym, assumes reporting and exception 
    handling has already been done
    """
    if u.user is None:
        return None
    return u.simulation

def add_superuser(db: Session = Depends(get_db)):
    """
    Creates the admin user. 
    TODO complete this. Does it hash the password?
    """
    superuser = User("admin", "insecure")
    superuser.is_superuser = True
    try:
        superuser = db.query(User).where(User.username == "Admin").first()
        if superuser != None:
            db.add(superuser)
            db.commit()
            return {"message": "Added superuser"}
    except Exception as error:
        logger.error ("Query failed looking for existing superuser",error)
    return {"message": "Superuser already exists"}

def authenticate_user(username: str, password: str, db: Session):
    """
    Primary authentication entry point.

    First checks that the user is in the database at all

    If this passes, checks the supplied password against the hashed 
    password in the database
    """
    user = get_user_from_username(username, db)
    if user == None:
        print(f"No record of user {username} was found in the database")
        return None
    if not pwd_context.verify(password, user.password):
        print(
            f"Though {username} was found, the supplied password {password} was not accepted"
        )
        return None
    return user

@router.get("/logout")
async def logout(u:usPair  = Depends(get_current_user_and_simulation), db: Session = Depends(get_db)):
    # Note: if we are not logged in, we won't be authenticated to log out, so we won't even reach this point
    print(f"Logging out user {u.user.username}")
    db.add(u.user)
    u.user.is_logged_in = False
    db.commit()
    return f"{u.user.username} logged out"

@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    """
    Responds to a login request received through the API.
    Authenticates the user
    """
    user: User = authenticate_user(form_data.username, form_data.password, db)
    if user == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # message=f"User {user.username} has logged in"
    logger.info("User %s has logged in",user.username)
    db.add(user)
    user.is_logged_in = True
    db.commit()
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", status_code=201)
def register(auth_details: AuthDetails, db: Session = Depends(get_db)):
    report(1, 1, f"Trying to add user called {auth_details.username}", db)
    try:
        already_registered = (
            db.query(User).where(User.username == auth_details.username).first()
            is not None
        )
        if already_registered:
            report(
                1,
                1,
                f"User  {auth_details.username} tried to register, but the name is taken",
                db,
            )
            return {
                "message": f"The name {auth_details.username} is taken: please try another name"
            }
        report(
            1,
            1,
            f"User {auth_details.username} not yet registered - will now be added",
            db,
        )
        new_user = User(auth_details.username, auth_details.password)
        db.add(new_user)
        db.commit()
        return {
            "message": f"User {new_user.username} added with hashed password {new_user.password}"
        }
    except Exception as error:
        report(1, 1, f"Error trying to add user {auth_details.username}: {error}", db)
        return {"message": "Server error"}

