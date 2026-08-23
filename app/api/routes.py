import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import db_dependency
from app.etl import run_pipeline
from app.schemas import (
    HealthResponse,
    JobResponse,
    SalaryInsightResponse,
    TechTrendResponse,
    TechTrendItem,
)
from app.services.analytics_service import (
    build_dashboard_analytics,
    get_city_comparison_data,
    get_role_demand_index,
    get_salary_insights_data,
    get_salary_trend_data,
    get_skill_growth_data,
    get_tech_trend_data,
    get_top_employers_data,
)

router = APIRouter()


@router.get("/", tags=["General"])
def home():
    return {"message": "Welcome to Job Market Pulse API. Visit /docs for OpenAPI specifications."}


@router.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check(db: db_dependency):
    """System health check endpoint verifying MongoDB ping response."""
    try:
        db.database.command("ping")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="ok" if db_status == "healthy" else "degraded",
        database=db_status,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


@router.get("/jobs/latest", response_model=List[JobResponse], tags=["Jobs"])
def get_latest_jobs(
    db: db_dependency,
    role: Optional[str] = Query(None, description="Filter jobs by role keyword (e.g. 'data engineer', 'python')"),
    city: Optional[str] = Query(None, description="Filter jobs by city ('chennai' or 'bangalore')"),
    limit: int = Query(10, ge=1, le=100),
):
    """Fetch recent job postings with optional role/city filtering."""
    query = {}

    if role:
        query["$or"] = [
            {"title": {"$regex": role, "$options": "i"}},
            {"searched_role": {"$regex": role, "$options": "i"}},
        ]

    if city:
        query["location"] = {"$regex": city, "$options": "i"}

    cursor = db.find(query).sort("created_at", -1).limit(limit)
    return list(cursor)


@router.get("/trends", response_model=TechTrendResponse, tags=["Analytics"])
def get_tech_trends(db: db_dependency, city: Optional[str] = Query(None)):
    """Return the top trending technologies by demand."""
    trend_data = get_tech_trend_data(db, city=city)
    return TechTrendResponse(status="success", data=[TechTrendItem(**item) for item in trend_data])


@router.get("/salaries", response_model=SalaryInsightResponse, tags=["Analytics"])
def get_salary_insights(db: db_dependency, role: str = "data engineer"):
    """Return average salary summary for a role."""
    payload = get_salary_insights_data(db, role=role)
    return SalaryInsightResponse(**payload)


@router.get("/analytics/dashboard", tags=["Analytics"])
def get_dashboard_analytics(db: db_dependency, city: Optional[str] = Query(None, description="Optional city filter for regional analytics.")):
    """Return dashboard metrics and chart-friendly payloads."""
    return build_dashboard_analytics(db, city=city)


@router.get("/analytics/salary-trends", tags=["Analytics"])
def get_salary_trends(
    db: db_dependency,
    role: Optional[str] = Query(None, description="Optional role filter."),
    city: Optional[str] = Query(None, description="Optional city filter."),
    days: int = Query(180, ge=30, le=3650),
):
    """Return monthly salary trend data over time."""
    return get_salary_trend_data(db, role=role, city=city, days=days)


@router.get("/analytics/city-comparison", tags=["Analytics"])
def get_city_comparison(
    db: db_dependency,
    role: Optional[str] = Query(None, description="Optional role filter."),
):
    """Compare cities by job volume and salary."""
    return get_city_comparison_data(db, role=role)


@router.get("/analytics/skill-growth", tags=["Analytics"])
def get_skill_growth(
    db: db_dependency,
    city: Optional[str] = Query(None, description="Optional city filter."),
    months: int = Query(6, ge=1, le=24),
):
    """Return monthly skill demand growth data."""
    return get_skill_growth_data(db, city=city, months=months)


@router.get("/analytics/role-demand-index", tags=["Analytics"])
def get_role_demand_index_endpoint(
    db: db_dependency,
    city: Optional[str] = Query(None, description="Optional city filter."),
):
    """Return normalized role demand scores for top roles."""
    return get_role_demand_index(db, city=city)


@router.get("/analytics/top-employers", tags=["Analytics"])
def get_top_employers(
    db: db_dependency,
    city: Optional[str] = Query(None, description="Optional city filter."),
    limit: int = Query(10, ge=1, le=25),
):
    """Return the companies with most job openings."""
    return get_top_employers_data(db, city=city, limit=limit)


@router.get("/run-manual-sync", tags=["Pipeline Execution"])
def sync_now():
    """Trigger manual execution of the ETL pipeline."""
    try:
        df = run_pipeline()
        return {"status": "success", "message": f"Pipeline executed successfully. Processed {len(df)} jobs."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ETL Execution failed: {str(e)}",
        )


@router.post("/admin/fix-metadata", tags=["Admin"], status_code=200)
def fix_missing_metadata(db: db_dependency):
    """Backfill missing `created_at` and coerce salary fields for existing job documents.

    This is a maintenance endpoint intended for development/testing environments
    to make analytics pipelines resilient when older documents lack expected fields.
    """
    try:
        import datetime as _dt

        now = _dt.datetime.now(_dt.timezone.utc)
        updated = 0

        # Find documents missing created_at or with created_at set to None
        cursor = db.find({"$or": [{"created_at": {"$exists": False}}, {"created_at": None}]})
        for doc in cursor:
            _id = doc.get("_id")
            if not _id:
                continue
            # Set created_at if missing
            db.update_one({"_id": _id}, {"$set": {"created_at": now}})
            updated += 1

        # Coerce salary fields stored as strings to numeric where possible
        cursor2 = db.find({"$or": [{"salary_min": {"$type": "string"}}, {"salary_max": {"$type": "string"}}]})
        for doc in cursor2:
            _id = doc.get("_id")
            if not _id:
                continue
            changed = {}
            try:
                sm = doc.get("salary_min")
                if isinstance(sm, str):
                    val = float(sm.replace(',', '').strip()) if sm.strip() else 0.0
                    changed["salary_min"] = val
            except Exception:
                pass
            try:
                sx = doc.get("salary_max")
                if isinstance(sx, str):
                    val = float(sx.replace(',', '').strip()) if sx.strip() else 0.0
                    changed["salary_max"] = val
            except Exception:
                pass

            if changed:
                db.update_one({"_id": _id}, {"$set": changed})
                updated += 1
        # Convert created_at stored as ISO strings into timezone-aware datetimes
        cursor3 = db.find({"created_at": {"$type": "string"}})
        for doc in cursor3:
            _id = doc.get("_id")
            if not _id:
                continue
            s = doc.get("created_at")
            try:
                # Parse ISO format and set UTC tz
                dt = __import__('datetime').datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=__import__('datetime').timezone.utc)
                db.update_one({"_id": _id}, {"$set": {"created_at": dt}})
                updated += 1
            except Exception:
                # ignore parse failures
                continue

        return {"status": "success", "updated_documents": updated}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/admin/sample-job", tags=["Admin"])
def sample_job(db: db_dependency):
    """Return a single job document (sanitized) for debugging analytics fields."""
    try:
        doc = db.find_one()
        if not doc:
            return {"status": "empty", "doc": None}

        # Sanitize ObjectId and non-serializable types
        safe = {}
        for k, v in doc.items():
            if k == "_id":
                safe["_id"] = str(v)
            else:
                safe[k] = v

        return {"status": "success", "doc": safe}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
