import datetime
from sqlalchemy import Column, String, Float, DateTime, Index
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    description = Column(String, nullable=True)
    salary_min = Column(Float, default=0.0)
    salary_max = Column(Float, default=0.0)
    tech_stack = Column(String, nullable=True, index=True)
    redirect_url = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        index=True
    )

Index("idx_job_title_salary", Job.title, Job.salary_min)