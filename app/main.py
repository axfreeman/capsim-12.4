from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .authorization import authroutes
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
    snippets,
    user,
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(actions.router)
app.include_router(authroutes.router)
app.include_router(buyers_and_sellers.router)
app.include_router(commodity.router)
app.include_router(industry.router)
app.include_router(simulation.router)
app.include_router(snippets.router)
app.include_router(socialClass.router)
app.include_router(stocks.router)
app.include_router(trace.router)
app.include_router(user.router)



@app.get("/")
# def root():
#     return {"message": "If you see this, the app is working. To view the API endpoints, append '/docs' to this URL"}
async def root():
    response = RedirectResponse(url='/docs')
    return response