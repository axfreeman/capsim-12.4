from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

SQLALCHEMY_DATABASE_URL =settings.sqlalchemy_database_url
# SQLALCHEMY_DATABASE_URL = "postgres://bmvaklphgfslok:c2f3ce2ffa34a28896394118327859bbb4e97b1eb2a72ce237a80d9fd8271ba8@ec2-3-230-24-12.compute-1.amazonaws.com:5432/d7leh83jqbeqof"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
