from fastapi import  HTTPException, Depends, APIRouter
from app.authorization.auth import Authentication_handler
from app.database import get_db
from app.models import User
from app.simulation.logging import report
from .. import schemas
from ..schemas import AuthDetails, UserOut
from sqlalchemy.orm import Session
from sqlalchemy.sql import exists


router=APIRouter(
    prefix="/auth",
    tags=['Authorization']
)

#TODO create one superuser at the start and don't allow any others
@router.post('/register', status_code=201)
def register(auth_details: schemas.AuthDetails,session: Session=Depends(get_db)):
    report(1,1,f"Trying to add user called {auth_details.username}",session)
    print("The auth_details object is",auth_details)
    # Check to see if the user is already there
    try:

        already_registered=session.query(User.username).filter_by(username=auth_details.username).first() is not None        
        print("query returned ", already_registered)
        if already_registered:
            report(1,1,f"User  {auth_details.username} already exists", session)
            return f"The name {auth_details.username} is taken: please try another name"
        report(1,1,f"User {auth_details.username} not yet registered - go ahead",session)
        hashed_password = Authentication_handler.get_password_hash(auth_details.password)
        new_user=User()
        new_user.password=hashed_password
        new_user.username=auth_details.username
        new_user.is_superuser=False
        session.add(new_user)
        session.commit()
        session.close()
        return f"User {auth_details.username} added"
    except Exception as error:
        report(1,1,f"Error trying to add user {auth_details.username}: {error}", session)
        return "Server error"
    

@router.post('/login')
def login(auth_details: AuthDetails,session: Session=Depends(get_db)):
    report(1,1,f"User {auth_details.username} wants to log in", session)
    user=session.query(User).filter_by(username=auth_details.username).first()
    user=session.query(User).filter_by(username=auth_details.username).first()
    if (user is None):
        report(1,1,f"User {auth_details.username} does not exist", session)
        raise HTTPException(status_code=401, detail=f"We dont have a record of user {auth_details.username}. Please register")
    # print(f"The user is {user}")
    # print(f"The password given was {auth_details.password}")
    # print(f"The password hash is {user.password}")
    if (not Authentication_handler.verify_password(auth_details.password, user.password)):
        report(1,1,f"User {auth_details.username} cannot log in", session)
        raise HTTPException(status_code=401, detail='Invalid username and/or password')
    report(1,1,f"User {auth_details.username} will be logged in", session)
    token = Authentication_handler.encode_token(auth_details.username)
    return { 'token': token }


@router.get('/unprotected')
def unprotected():
    return { 'hello': 'world' }


@router.get('/protected')
def protected(username=Depends(Authentication_handler.auth_wrapper)):
    return { 'name': username }

# TODO only superusers should be able to see this
@router.get("/users",response_model=UserOut)
def get_users(db: Session = Depends (get_db)):
    users=db.query(User).all()
    print(users) 
    return users

