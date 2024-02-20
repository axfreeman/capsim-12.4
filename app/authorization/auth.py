from jose import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.simulation.logging import report
from ..models import Simulation, User
from ..database  import get_db  
from passlib.context import CryptContext
from app.models import Simulation
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta

class AuthHandler():
    security = HTTPBearer()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret = 'SECRET'

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_password):
        # print (f"call to verify password with {plain_password} and hash {hashed_password}")
        return self.pwd_context.verify(plain_password, hashed_password)

    def encode_token(self, user_id):
        payload = {
            'exp': datetime.utcnow() + timedelta(days=0, minutes=5),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            self.secret,
            algorithm='HS256'
        )

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Signature has expired')
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail='Invalid token')

    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
        return self.decode_token(auth.credentials)

Authentication_handler = AuthHandler()

def get_current_simulation(db: Session=Depends(get_db), username=Depends(Authentication_handler.auth_wrapper)):
    me=db.query(User).filter(User.username==username).first()     
    if (me==None):
        print(f"ERROR: user {username} does not exist ")
        return None
    # report(2,0,f"User {username} with id {me.id} is logged in ",db)
    simulation=db.query(Simulation).filter(Simulation.user_id==me.id).first()
    if (simulation==None):
        print(f"User {username} with id {me.id} has no simulations ")
        return None
    report(3,simulation.id,f"User {me.username} with id {me.id} is logged in and is using simulation id {simulation.id}",db)
    return simulation

