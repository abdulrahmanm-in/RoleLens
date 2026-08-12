import datetime
import logging
import time
from typing import List, Dict, Any, Optional

import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from pymongo import UpdateOne
from pymongo.collection import Collection

from app.config import APP_ID, APP_KEY
from app.dependencies import get_db

# -------------------------------------------------------------------
# Structured Logging Setup
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ETL_Pipeline")

# -------------------------------------------------------------------
# HTTP Session with Retry / Backoff Strategy
# -------------------------------------------------------------------
def get_http_session() -> requests.Session:
    """Configures a requests session with exponential backoff and retries."""
    session = requests.Session()
    
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    session.headers.update({
        "User-Agent": "RoleLens-ETL/1.0 (Data Engineering Project)"
    })
    
    return session

# -------------------------------------------------------------------
# 1. EXTRACT (All IT Jobs across Cities)
# -------------------------------------------------------------------
def fetch_all_it_jobs(
    cities: Optional[List[str]] = None,
    max_pages: int = 5
) -> List[Dict[str, Any]]:
    """
    Extracts ALL IT & Tech job postings for target cities using 
    Adzuna's category filter sorted by date.
    """
    session = get_http_session()
    all_results: List[Dict[str, Any]] = []

    if not APP_ID or not APP_KEY:
        logger.error("ADZUNA_APP_ID or ADZUNA_APP_KEY environment variables are missing!")
        return []

    # avoid mutable default argument
    cities = cities or ["chennai", "bangalore"]

    for city in cities:
        logger.info(f"🌐 Starting extraction for ALL IT Jobs in location='{city.title()}, IN'")

        for page in range(1, max_pages + 1):
            url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}"
            params = {
                "app_id": APP_ID,
                "app_key": APP_KEY,
                "results_per_page": 50,
                "where": city,
                "category": "it-jobs",
                "sort_by": "date"
            }

            try:
                logger.info(f"Fetching page {page}/{max_pages} for {city.title()}...")
                response = session.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    logger.info(f"No more results found for {city.title()} on page {page}.")
                    break

                # Tag metadata for city query tracking
                for item in results:
                    item['searched_city'] = city

                all_results.extend(results)
                logger.info(f"Successfully retrieved {len(results)} jobs for {city.title()} (Page {page}).")
                time.sleep(0.3)

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch data for {city.title()} on page {page}: {str(e)}")
                break

    logger.info(f"Total raw IT jobs extracted across all target cities: {len(all_results)}")
    return all_results

# -------------------------------------------------------------------
# 2. TRANSFORM
# -------------------------------------------------------------------
def transform_data(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Cleans, normalizes, extracts tech stacks, and deduplicates raw job payloads."""
    if not raw_data:
        logger.warning("Transform stage received an empty raw dataset.")
        return pd.DataFrame()

    df = pd.json_normalize(raw_data)

    # 1. Keep key fields
    cols_to_keep = [
        'id', 'title', 'company.display_name', 'location.display_name',
        'description', 'salary_min', 'salary_max', 'redirect_url', 'searched_city'
    ]
    df = df[[c for c in cols_to_keep if c in df.columns]]

    # 2. Rename columns
    df = df.rename(columns={
        'company.display_name': 'company',
        'location.display_name': 'location'
    })

    # 3. Clean salary fields
    if 'salary_min' in df.columns:
        df['salary_min'] = pd.to_numeric(df['salary_min'], errors='coerce').fillna(0.0)
    else:
        df['salary_min'] = 0.0

    if 'salary_max' in df.columns:
        df['salary_max'] = pd.to_numeric(df['salary_max'], errors='coerce').fillna(0.0)
    else:
        df['salary_max'] = 0.0

    # 4. Extract tech keywords from job description
    target_keywords = [
        'python', 'sql', 'aws', 'docker', 'fastapi', 'pandas',
        'spark', 'airflow', 'kafka', 'postgres', 'azure', 'gcp', 'dbt'
    ]
    
    def parse_tech_stack(text_content: Any) -> str:
        text_str = str(text_content).lower() if pd.notnull(text_content) else ""
        matched = [kw for kw in target_keywords if kw in text_str]
        return ",".join(matched)

    if 'description' in df.columns:
        df['tech_stack'] = df['description'].apply(parse_tech_stack)
    else:
        df['tech_stack'] = ""

    # 5. Clean string fields
    for col in ['title', 'company', 'location', 'description', 'redirect_url', 'searched_city']:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("N/A")

    # 6. Deduplicate by unique Adzuna job ID
    df['id'] = df['id'].astype(str)
    initial_count = len(df)
    df = df.drop_duplicates(subset=['id'])
    logger.info(f"Transformation complete. Cleaned {len(df)} jobs (Dropped {initial_count - len(df)} duplicates).")

    return df

# -------------------------------------------------------------------
# 3. LOAD (MongoDB 7-Day Retention & Bulk Upsert)
# -------------------------------------------------------------------
def load_data(df: pd.DataFrame, target_collection: Optional[Collection] = None) -> int:
    """Loads transformed DataFrame into MongoDB Atlas while purging listings older than 7 days."""
    if df.empty:
        logger.info("Load skipped: Transformed DataFrame is empty.")
        return 0

    collection = target_collection if target_collection is not None else get_db()
    utc_now = datetime.datetime.now(datetime.timezone.utc)

    try:
        # Step 1: Enforce 7-day rolling retention window
        logger.info("Executing 7-day rolling window cleanup in MongoDB...")
        seven_days_ago = utc_now - datetime.timedelta(days=7)
        delete_result = collection.delete_many({"created_at": {"$lt": seven_days_ago}})
        logger.info(f"🧹 Purged {delete_result.deleted_count} job listings older than 7 days.")

        # Step 2: Prepare documents and bulk upsert operations
        records = df.to_dict(orient="records")
        bulk_operations = []

        for record in records:
            job_id = str(record.pop("id"))
            # Build the document that will be $set (exclude immutable _id and timestamps)
            doc_to_set = {k: v for k, v in record.items() if k not in ("_id", "created_at")}

            # Use $setOnInsert for created_at to preserve original create time on upserts
            bulk_operations.append(
                UpdateOne(
                    {"_id": job_id},
                    {"$set": doc_to_set, "$setOnInsert": {"created_at": utc_now}},
                    upsert=True
                )
            )

        # Step 3: Execute MongoDB Bulk Write
        if bulk_operations:
            result = collection.bulk_write(bulk_operations)
            inserted_or_updated = result.upserted_count + result.modified_count
            logger.info(f"✅ Successful Mongo Load: {result.upserted_count} inserted, {result.modified_count} updated.")
            return inserted_or_updated

        return 0

    except Exception as e:
        logger.error("❌ ETL Load to MongoDB failed (see exc_info)", exc_info=True)
        raise

# -------------------------------------------------------------------
# Pipeline Orchestrator
# -------------------------------------------------------------------
def run_pipeline() -> pd.DataFrame:
    """Executes the full Extract-Transform-Load (ETL) pipeline lifecycle."""
    logger.info("🚀 Initiating daily Job Market Pulse ETL Pipeline run...")
    
    target_cities = ["chennai", "bangalore"]
    
    raw_jobs = fetch_all_it_jobs(cities=target_cities, max_pages=5)
    clean_df = transform_data(raw_jobs)
    load_data(clean_df)
    
    logger.info("🏁 Daily ETL Pipeline execution completed successfully.")
    return clean_df


if __name__ == "__main__":
    run_pipeline()