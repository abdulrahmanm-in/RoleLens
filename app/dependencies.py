from typing import Annotated
from fastapi import Depends
from pymongo.collection import Collection
from app.database import jobs_collection

def get_db():
    return jobs_collection

db_dependency = Annotated[Collection, Depends(get_db)]