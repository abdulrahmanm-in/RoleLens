import datetime
from typing import Any, Dict, List, Optional

from app.analytics import (
    get_job_volume_chart,
    get_role_distribution_chart,
    get_salary_by_role_chart,
)


def _build_city_match(city: Optional[str] = None) -> Dict[str, Any]:
    """Build a MongoDB filter for a city match when provided."""
    match = {}
    if city:
        match["location"] = {"$regex": city, "$options": "i"}
    return match


def _count_jobs(db, query: Dict[str, Any]) -> int:
    """Count documents in a collection without assuming count_documents exists."""
    result = list(db.aggregate([
        {"$match": query},
        {"$count": "total_jobs"}
    ]))
    if not result:
        return 0
    return int(result[0].get("total_jobs", 0))


def _average_salary(db, query: Dict[str, Any], field_name: str) -> float | str:
    """Return average salary for a field, or 'N/A' if there are no matching jobs."""
    pipeline = [
        {"$match": query},
        {"$group": {"_id": None, field_name: {"$avg": f"${field_name}"}}}
    ]
    result = list(db.aggregate(pipeline))
    if not result or not result[0].get(field_name):
        return "N/A"
    return round(float(result[0][field_name]), 2)


def get_tech_trend_data(db, city: Optional[str] = None, limit: int = 10):
    """Return top technologies by demand."""
    match_stage = {"tech_stack": {"$ne": "", "$exists": True}}
    if city:
        match_stage["location"] = {"$regex": city, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {"$project": {"tech": {"$split": ["$tech_stack", ","]}}},
        {"$unwind": "$tech"},
        {"$group": {"_id": "$tech", "demand_count": {"$sum": 1}}},
        {"$sort": {"demand_count": -1}},
        {"$limit": limit},
    ]

    results = list(db.aggregate(pipeline))
    return [
        {"tech_stack": str(r["_id"]).strip(), "demand_count": int(r["demand_count"])}
        for r in results if str(r.get("_id", "")).strip()
    ]


def get_salary_insights_data(db, role: str = "data engineer"):
    """Return salary summary for a role."""
    pipeline = [
        {"$match": {"title": {"$regex": role, "$options": "i"}, "salary_min": {"$gt": 0}}},
        {"$group": {"_id": None, "avg_min": {"$avg": "$salary_min"}, "avg_max": {"$avg": "$salary_max"}}},
    ]

    results = list(db.aggregate(pipeline))
    if results and results[0]:
        raw_min = results[0].get("avg_min")
        raw_max = results[0].get("avg_max")
        avg_min = round(raw_min, 2) if raw_min is not None else "N/A"
        avg_max = round(raw_max, 2) if raw_max is not None else "N/A"
    else:
        avg_min = "N/A"
        avg_max = "N/A"

    return {
        "status": "success",
        "role": role,
        "avg_min_salary": avg_min,
        "avg_max_salary": avg_max,
    }


def get_salary_trend_data(db, role: Optional[str] = None, city: Optional[str] = None, days: int = 180):
    """Return monthly avg salary trend over a recent time window."""
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    match_stage = {"created_at": {"$gte": start_date}, "salary_min": {"$gt": 0}}

    if role:
        match_stage["title"] = {"$regex": role, "$options": "i"}
    if city:
        match_stage["location"] = {"$regex": city, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {"$project": {"period": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}}, "avg_min": "$salary_min", "avg_max": "$salary_max"}},
        {"$group": {"_id": "$period", "avg_min_salary": {"$avg": "$avg_min"}, "avg_max_salary": {"$avg": "$avg_max"}}},
        {"$sort": {"_id": 1}},
    ]

    results = list(db.aggregate(pipeline))
    return {
        "status": "success",
        "role": role or "all",
        "city": city or "all",
        "data": [
            {
                "period": record["_id"],
                "avg_min_salary": round(float(record.get("avg_min_salary", 0)), 2),
                "avg_max_salary": round(float(record.get("avg_max_salary", 0)), 2),
            }
            for record in results
        ],
    }


def get_city_comparison_data(db, role: Optional[str] = None):
    """Compare jobs and salary by city."""
    match_stage = {"location": {"$exists": True, "$ne": ""}, "salary_min": {"$gt": 0}}
    if role:
        match_stage["title"] = {"$regex": role, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": "$location",
            "job_count": {"$sum": 1},
            "avg_min_salary": {"$avg": "$salary_min"},
            "avg_max_salary": {"$avg": "$salary_max"},
        }},
        {"$sort": {"job_count": -1}},
        {"$limit": 10},
    ]

    results = list(db.aggregate(pipeline))
    return {
        "status": "success",
        "role": role or "all",
        "data": [
            {
                "city": str(record["_id"]).strip(),
                "job_count": int(record.get("job_count", 0)),
                "avg_min_salary": round(float(record.get("avg_min_salary", 0)), 2),
                "avg_max_salary": round(float(record.get("avg_max_salary", 0)), 2),
            }
            for record in results if str(record.get("_id", "")).strip()
        ],
    }


def get_skill_growth_data(db, city: Optional[str] = None, months: int = 6):
    """Return recent monthly skill demand growth by technology."""
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=months * 30)
    match_stage = {"created_at": {"$gte": start_date}, "tech_stack": {"$ne": "", "$exists": True}}
    if city:
        match_stage["location"] = {"$regex": city, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {"$project": {
            "month": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
            "tech": {"$split": ["$tech_stack", ","]}
        }},
        {"$unwind": "$tech"},
        {"$group": {
            "_id": {"month": "$month", "tech": {"$trim": {"input": "$tech"}}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.month": 1, "count": -1}},
    ]

    results = list(db.aggregate(pipeline))
    data = []
    for record in results:
        tech_name = str(record["_id"].get("tech", "")).strip()
        if not tech_name:
            continue
        data.append({
            "period": record["_id"]["month"],
            "tech_stack": tech_name,
            "count": int(record.get("count", 0)),
        })
    return {"status": "success", "city": city or "all", "data": data}


def get_role_demand_index(db, city: Optional[str] = None):
    """Return a normalized role demand index based on title frequency."""
    match_stage = {"title": {"$exists": True, "$ne": ""}}
    if city:
        match_stage["location"] = {"$regex": city, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {"$group": {"_id": "$title", "job_count": {"$sum": 1}}},
        {"$sort": {"job_count": -1}},
        {"$limit": 20},
    ]

    results = list(db.aggregate(pipeline))
    max_count = max((int(r.get("job_count", 0)) for r in results), default=0)
    data = []
    for record in results:
        role = str(record.get("_id", "")).strip()
        if not role:
            continue
        job_count = int(record.get("job_count", 0))
        demand_index = round((job_count / max_count) * 100, 2) if max_count else 0
        data.append({"role": role, "job_count": job_count, "demand_index": demand_index})

    return {"status": "success", "city": city or "all", "data": data}


def get_top_employers_data(db, city: Optional[str] = None, limit: int = 10):
    """Return top employers by number of openings."""
    match_stage = {"company": {"$exists": True, "$ne": ""}}
    if city:
        match_stage["location"] = {"$regex": city, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {"$group": {"_id": "$company", "openings": {"$sum": 1}}},
        {"$sort": {"openings": -1}},
        {"$limit": limit},
    ]

    results = list(db.aggregate(pipeline))
    return {
        "status": "success",
        "city": city or "all",
        "data": [
            {"company": str(record["_id"]).strip(), "openings": int(record.get("openings", 0))}
            for record in results if str(record.get("_id", "")).strip()
        ],
    }


def build_dashboard_analytics(db, city: Optional[str] = None) -> Dict[str, Any]:
    """Build a full dashboard payload with summary and chart-friendly data."""
    query = _build_city_match(city)
    summary = {
        "total_jobs": _count_jobs(db, query),
        "avg_min_salary": _average_salary(db, {**query, "salary_min": {"$gt": 0}}, "salary_min"),
        "avg_max_salary": _average_salary(db, {**query, "salary_max": {"$gt": 0}}, "salary_max"),
    }

    return {
        "status": "success",
        "city": city or "all",
        "summary": summary,
        "charts": {
            "tech_trends": {
                "type": "bar",
                "title": "Top skill demand",
                "labels": [entry["tech_stack"] for entry in get_tech_trend_data(db, city=city)],
                "values": [entry["demand_count"] for entry in get_tech_trend_data(db, city=city)],
            },
            "job_volume": {
                **get_job_volume_chart(db, city=city),
            },
            "role_distribution": {
                **get_role_distribution_chart(db, city=city),
            },
            "salary_by_role": {
                **get_salary_by_role_chart(db, city=city),
            },
        },
    }
