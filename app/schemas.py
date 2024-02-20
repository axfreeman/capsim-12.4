from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuthDetails(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    id: int
    password: str
    username: str
    is_superuser: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    password: str


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class SimulationBase(BaseModel):
    id: int


class SimulationMinimal(BaseModel):
    name: str


class SimulationOut(SimulationBase):
    user_id: int
    name: str
    time_stamp: int
    state: str
    periods_per_year: float
    population_growth_rate: float
    investment_ratio: float
    currency_symbol: str
    quantity_symbol: str
    melt: float
    owner: UserOut

    class Config:
        from_attributes = True


class SimulationCreate(SimulationBase):
    pass

    class Config:
        from_attributes = True


class CommodityBase(BaseModel):
    id: int
    simulation_id: int
    name: str
    origin: str
    usage: str
    size: float
    total_value: float
    total_price: float
    unit_value: float
    unit_price: float
    turnover_time: float
    demand: float
    supply: float
    allocation_ratio: float
    display_order: int
    image_name: str
    tooltip: str
    monetarily_effective_demand: float
    investment_proportion: float
    simulation_name: SimulationMinimal

class CommodityMinimal(BaseModel):
    name: str
    origin: str
    usage: str

class IndustryBase(BaseModel):
    id: int
    name: str
    simulation_id: int
    output: str
    output_scale: float
    output_growth_rate: float
    initial_capital: float
    work_in_progress: float
    current_capital: float
    profit: float
    profit_rate: float

class IndustryMinimal(BaseModel):
    name:str

class TraceOut(BaseModel):
    id: int
    simulation_id: int
    time_stamp: int
    level :int
    message: str

class SocialClassBase(BaseModel):
    id: int
    simulation_id: int
    name: str
    population: float
    participation_ratio: float
    consumption_ratio: float
    revenue: float
    assets: float

class SocialClassMinimal(BaseModel):
    name:str

class socialStocksBase(BaseModel):
    __tablename__ = "social_stocks"

    id: int
    owner_id: int
    usage_type: str
    size: float
    requirement: float
    simulation_id: int
    commodity_id: int
    demand: float

class industryStocksBase(BaseModel):
    __tablename__ = "industry_stocks"

    id: int
    owner_id: int
    usage_type: str
    size: float
    requirement: float
    simulation_id: int
    commodity_id: int
    demand: float

class stocksBase(BaseModel):
    __tablename__="stocks"

    id: int
    simulation_id:int
    owner_id: int
    commodity_id:int
    owner_type:str
    name:str
    usage_type: str
    size: float
    value: float
    price: float
    requirement: float
    demand: float

class BuyerBase(BaseModel):
    __tablename__ = "buyers"

    id: int
    simulation_id: int 
    owner_type: str
    purchase_stock_id: int
    money_stock_id: int
    commodity_id: int

class SellerBase(BaseModel):
    __tablename__ = "sellers"

    id: int
    simulation_id: int 
    owner_type: str
    sales_stock_id: int
    money_stock_id: int
    commodity_id: int


class UploadIn(BaseModel):
    file: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None
