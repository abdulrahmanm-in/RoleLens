import datetime
from typing import Any, Dict, Optional


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


def get_tech_trend_chart(db, city: Optional[str] = None, limit: int = 8) -> Dict[str, Any]:
    """Return technology demand data in chart-ready format."""
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
    labels = []
    values = []
    for record in results:
        tech_name = str(record.get("_id", "")).strip()
        if not tech_name:
            continue
        labels.append(tech_name)
        values.append(int(record.get("demand_count", 0)))

    return {
        "type": "bar",
        "title": "Top skill demand",
        "labels": labels,
        "values": values,
    }


def get_job_volume_chart(db, city: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """Return a date-based job volume chart for recent postings."""
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    match_stage = {"created_at": {"$gte": start_date}}
    if city:
        match_stage["location"] = {"$regex": city, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {"$project": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}}},
        {"$group": {"_id": "$date", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]

    results = list(db.aggregate(pipeline))
    labels = [record["_id"] for record in results]
    values = [int(record["count"]) for record in results]

    return {
        "type": "line",
        "title": "Job volume by day",
        "labels": labels,
        "values": values,
    }


def get_role_distribution_chart(db, city: Optional[str] = None, limit: int = 8) -> Dict[str, Any]:
    """Return top roles by posting count."""
    match_stage = {"title": {"$exists": True, "$ne": ""}}
    if city:
        match_stage["location"] = {"$regex": city, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {"$group": {"_id": "$title", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]

    results = list(db.aggregate(pipeline))
    labels = [str(record["_id"]).strip() for record in results if record.get("_id")]
    values = [int(record["count"]) for record in results]

    return {
        "type": "pie",
        "title": "Role distribution",
        "labels": labels,
        "values": values,
    }


def get_salary_by_role_chart(db, city: Optional[str] = None, limit: int = 6) -> Dict[str, Any]:
    """Return average salary by role for comparison."""
    match_stage = {"salary_min": {"$gt": 0}, "title": {"$exists": True, "$ne": ""}}
    if city:
        match_stage["location"] = {"$regex": city, "$options": "i"}

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": "$title",
            "avg_min_salary": {"$avg": "$salary_min"},
            "avg_max_salary": {"$avg": "$salary_max"},
        }},
        {"$sort": {"avg_max_salary": -1}},
        {"$limit": limit},
    ]

    results = list(db.aggregate(pipeline))
    labels = [str(record["_id"]).strip() for record in results if record.get("_id")]
    min_values = [round(float(record.get("avg_min_salary", 0)), 2) for record in results]
    max_values = [round(float(record.get("avg_max_salary", 0)), 2) for record in results]

    return {
        "type": "scatter",
        "title": "Average salary by role",
        "labels": labels,
        "min_values": min_values,
        "max_values": max_values,
    }


def build_dashboard_analytics(db, city: Optional[str] = None) -> Dict[str, Any]:
    """Build a complete analytics payload for dashboard charts and summary metrics."""
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
            "tech_trends": get_tech_trend_chart(db, city=city),
            "job_volume": get_job_volume_chart(db, city=city),
            "role_distribution": get_role_distribution_chart(db, city=city),
            "salary_by_role": get_salary_by_role_chart(db, city=city),
        },
    }
