"""Provides endpoints for login, logout, registration, and user management."""

from datetime import timedelta
import http
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import  OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.authorization.auth import ACCESS_TOKEN_EXPIRE_MINUTES, User, authenticate_user, create_access_token, get_current_user_and_simulation, usPair
from ..database import get_db
from ..simulation.logging import report
from ..schemas import AuthDetails, ServerMessage, Token, UserBase
from ..reporting.caplog import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    """Endpoint for a login request received through the API.
    Authenticates by checking user exists and supplied the right password.
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
    logger.info("User %s has logged in",user.username)
    db.add(user)
    user.is_logged_in = True
    db.commit()
    return Token(access_token=access_token, token_type="bearer")

@router.get("/logout",response_model=ServerMessage)
async def logout(u:usPair  = Depends(get_current_user_and_simulation), db: Session = Depends(get_db)):
    """Endpoint logs out the currently logged-in user.

    Crude method: simply sets is_logged_in to false.

    Note this means the authentication procedures must check user status
    in addition to invoking fastAPI security.
    
    TODO If  invoked by somebody who is not logged in, should do nothing.
    """
    if u==None:
        return {"message":f"Non-existent user tried to log out"}
    print(f"Trying to log a user out, probably called {u.user.username}")
    db.add(u.user)
    u.user.is_logged_in = False
    db.commit()
    return {"message":f"{u.user.username} logged out","statusCode":status.HTTP_100_CONTINUE}

@router.post("/register")
async def register_new_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> ServerMessage:
    """Endpoint for a registration request received through the API.
    Assumes that the front end has parsed the form data and that it
    contains a username and password of some kind. 

    So only checks whether the user already exists.

    Reports any server error.
    """
    # user: User = authenticate_user(form_data.username, form_data.password, db)
    username=form_data.username
    password=form_data.password
    logger.info("User %s is asking to register",username)
    print(f"password supplied was {password}") # TODO Get rid of this once the code is tested.
    try:
        if db.query(User).where(User.username == username).first() is not None:
            report(1,1,f"User  {username} tried to register, but the name is taken",db,)
            return {"message":f"{username} is already registered","statusCode":status.HTTP_409_CONFLICT}
        report(1,1,f"User {username} will now be added",db,)
        new_user = User(username, password) # the User class will hash this password
        db.add(new_user)
        db.commit()
        return {"message":f"{username} registered","statusCode":status.HTTP_200_OK}
    except Exception as error:
        report(1, 1, f"Error trying to register user {username}: {error}", db)
        return {"message":f"Error {error} trying to register {username} ","statusCode":status.HTTP_400_BAD_REQUEST}

@router.get("/{username}",response_model=UserBase)
def get_user(username: str, db: Session = Depends(get_db)):
    """Return the user object for the user called username.
    TODO should be restricted to admin.
    TODO under development.
    """
    user = db.query(User).filter(User.username == username).first()
    return user

