import datetime
from typing import List
from fastapi import FastAPI, HTTPException, status
from sqlalchemy import desc, func
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.etl import run_pipeline
from app.models import Job
from app.dependencies import db_dependency
from app.schemas import HealthResponse, JobResponse, TechTrendResponse, TechTrendItem, SalaryInsightResponse

# Ensure tables are created
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# Scheduler & Lifespan
# ---------------------------------------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(run_pipeline, 'interval', hours=24)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⏰ Scheduler starting...")
    scheduler.start()
    yield
    print("⏰ Scheduler shutting down...")
    scheduler.shutdown()

app = FastAPI(
    title="Job Market Pulse API",
    description="Live job market insights and ETL analytics for Chennai, India.",
    version="1.0.0",
    lifespan=lifespan
)

# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@app.get("/", tags=["General"])
def home():
    return {"message": "Welcome to Job Market Pulse API. Visit /docs for OpenAPI specifications."}

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check(db: db_dependency):
    """System health check endpoint verifying DB connectivity."""
    try:
        db.execute(func.now())
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        
    return HealthResponse(
        status="ok" if db_status == "healthy" else "degraded",
        database=db_status,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

@app.get("/jobs/latest", response_model=List[JobResponse], tags=["Jobs"])
def get_latest_jobs(db: db_dependency, limit: int = 10):
    """Fetch recent job postings sorted by ingestion time."""
    jobs = db.query(Job).order_by(desc(Job.created_at)).limit(limit).all()
    return jobs

@app.get("/trends", response_model=TechTrendResponse, tags=["Analytics"])
def get_tech_trends(db: db_dependency):
    """Aggregated skill demand metrics."""
    results = (
        db.query(Job.tech_stack, func.count(Job.id).label("demand_count"))
        .filter(Job.tech_stack != "", Job.tech_stack.isnot(None))
        .group_by(Job.tech_stack)
        .order_by(desc("demand_count"))
        .limit(5)
        .all()
    )
    
    data = [TechTrendItem(tech_stack=r[0], demand_count=r[1]) for r in results]
    return TechTrendResponse(status="success", data=data)

@app.get("/salaries", response_model=SalaryInsightResponse, tags=["Analytics"])
def get_salary_insights(db: db_dependency, role: str = "data engineer"):
    """Fetch average minimum and maximum salaries by role."""
    result = (
        db.query(
            func.avg(Job.salary_min).label("avg_min"),
            func.avg(Job.salary_max).label("avg_max")
        )
        .filter(Job.title.ilike(f"%{role}%"))
        .filter(Job.salary_min > 0)
        .first()
    )
    
    avg_min = round(result.avg_min, 2) if result and result.avg_min else "N/A"
    avg_max = round(result.avg_max, 2) if result and result.avg_max else "N/A"
    
    return SalaryInsightResponse(
        status="success",
        role=role,
        avg_min_salary=avg_min,
        avg_max_salary=avg_max
    )

@app.get("/run-manual-sync", tags=["Pipeline Execution"])
def sync_now():
    """Trigger manual execution of the ETL pipeline."""
    try:
        df = run_pipeline()
        return {"status": "success", "message": f"Pipeline executed successfully. Processed {len(df)} jobs."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ETL Execution failed: {str(e)}"
        )