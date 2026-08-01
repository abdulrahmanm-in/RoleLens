import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    id: str
    title: str
    company: Optional[str] = "N/A"
    location: Optional[str] = "N/A"
    tech_stack: Optional[str] = ""
    salary_min: float
    salary_max: float
    redirect_url: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class TechTrendItem(BaseModel):
    tech_stack: str
    demand_count: int


class TechTrendResponse(BaseModel):
    status: str
    data: List[TechTrendItem]


class SalaryInsightResponse(BaseModel):
    status: str
    role: str
    avg_min_salary: Union[float, str]
    avg_max_salary: Union[float, str]


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime.datetime