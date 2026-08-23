import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from app.api.routes import router as api_router
from app.etl import run_pipeline

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
    lifespan=lifespan,
)

app.include_router(api_router)