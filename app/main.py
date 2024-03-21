from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .database import Base, engine
from .routers import (
    actions,
    commodity,
    industry,
    login,
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
interface.include_router(login.router)
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