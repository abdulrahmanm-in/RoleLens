import datetime
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

from app.etl import run_pipeline
from app.dependencies import db_dependency
from app.schemas import (
    HealthResponse, 
    JobResponse, 
    TechTrendResponse, 
    TechTrendItem, 
    SalaryInsightResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rolelens")

# ---------------------------------------------------------
# Scheduler & Lifespan
# ---------------------------------------------------------
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(
    run_pipeline,
    'interval',
    hours=24,
    id='daily_rolelens_sync',
    replace_existing=True,
    misfire_grace_time=3600,
    coalesce=True,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("⏰ Scheduler starting...")
    if not scheduler.running:
        scheduler.start()
    logger.info("Scheduled jobs: %s", [job.id for job in scheduler.get_jobs()])
    try:
        yield
    finally:
        logger.info("⏰ Scheduler shutting down...")
        scheduler.shutdown(wait=False)

app = FastAPI(
    title="RoleLens API",
    description="Automated job market analytics and skill extraction pipeline powered by MongoDB",
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
    """System health check endpoint verifying MongoDB ping response."""
    try:
        # Ping MongoDB database to confirm active connection
        db.database.command("ping")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        
    return HealthResponse(
        status="ok" if db_status == "healthy" else "degraded",
        database=db_status,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )


@app.get("/jobs/latest", response_model=List[JobResponse], tags=["Jobs"])
def get_latest_jobs(
    db: db_dependency, 
    role: Optional[str] = Query(None, description="Filter jobs by role keyword (e.g. 'data engineer', 'python')"),
    city: Optional[str] = Query(None, description="Filter jobs by city ('chennai' or 'bangalore')"),
    limit: int = Query(10, ge=1, le=100)
):
    """Fetch recent job postings with optional role/city filtering."""
    query = {}
    
    if role:
        query["$or"] = [
            {"title": {"$regex": role, "$options": "i"}},
            {"searched_role": {"$regex": role, "$options": "i"}}
        ]
    
    if city:
        query["location"] = {"$regex": city, "$options": "i"}

    # Query MongoDB collection
    cursor = db.find(query).sort("created_at", -1).limit(limit)
    jobs = list(cursor)

    return jobs


@app.get("/trends", response_model=TechTrendResponse, tags=["Analytics"])
def get_tech_trends(db: db_dependency, city: Optional[str] = Query(None)):
    """
    Calculates top trending technologies from ALL job postings in the 7-day window.
    """
    match_stage = {"tech_stack": {"$ne": "", "$exists": True}}
    if city:
        match_stage["location"] = {"$regex": city, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        # Split comma-separated tech stacks (e.g. "python,sql,aws" -> ["python", "sql", "aws"])
        {"$project": {"tech": {"$split": ["$tech_stack", ","]}}},
        {"$unwind": "$tech"},
        {"$group": {"_id": "$tech", "demand_count": {"$sum": 1}}},
        {"$sort": {"demand_count": -1}},
        {"$limit": 10}
    ]
    
    results = list(db.aggregate(pipeline))
    data = [TechTrendItem(tech_stack=r["_id"], demand_count=r["demand_count"]) for r in results]
    
    return TechTrendResponse(status="success", data=data)


@app.get("/salaries", response_model=SalaryInsightResponse, tags=["Analytics"])
def get_salary_insights(db: db_dependency, role: str = "data engineer"):
    """Fetch average minimum and maximum salaries for a specific role."""
    pipeline = [
        {
            "$match": {
                "title": {"$regex": role, "$options": "i"},
                "salary_min": {"$gt": 0}
            }
        },
        {
            "$group": {
                "_id": None,
                "avg_min": {"$avg": "$salary_min"},
                "avg_max": {"$avg": "$salary_max"}
            }
        }
    ]
    
    results = list(db.aggregate(pipeline))

    # Handle None values returned by aggregation engines (mongomock may return None)
    if results and results[0]:
        raw_min = results[0].get("avg_min")
        raw_max = results[0].get("avg_max")

        avg_min = round(raw_min, 2) if raw_min is not None else "N/A"
        avg_max = round(raw_max, 2) if raw_max is not None else "N/A"
    else:
        avg_min = "N/A"
        avg_max = "N/A"
    
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