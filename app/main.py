from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
from .authorization import auth
from .database import Base, engine
from .routers import (
    actions,
    buyers_and_sellers,
    commodity,
    industry,
    simulation,
    socialClass,
    stocks,
    trace,
    user,
)

Base.metadata.create_all(bind=engine)
# auth.add_superuser() # TODO not working - add the admin user by hand for now
interface = FastAPI()

interface.include_router(actions.router)
interface.include_router(auth.router)
interface.include_router(buyers_and_sellers.router)
interface.include_router(commodity.router)
interface.include_router(industry.router)
interface.include_router(simulation.router)
interface.include_router(socialClass.router)
interface.include_router(stocks.router)
interface.include_router(trace.router)
interface.include_router(user.router)

@interface.get("/")
# def root():
#     return {"message": "If you see this, the app is working. To view the API endpoints, append '/docs' to this URL"}
async def root():
    response = RedirectResponse(url='/docs')
    return response