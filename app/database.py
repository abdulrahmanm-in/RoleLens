from pymongo import MongoClient
from app.config import DATABASE_URL 

client = MongoClient(DATABASE_URL)
db = client["rolelens-db"]
jobs_collection = db["jobs"]