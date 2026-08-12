import pytest
from fastapi.testclient import TestClient
import mongomock

from app.main import app
from app.dependencies import get_db


class _TestCollectionWrapper:
    """Wrap mongomock collection to provide a minimal `database.command('ping')` implementation
    expected by the health endpoint while delegating CRUD/aggregation calls to the real collection.
    """
    def __init__(self, coll):
        self._coll = coll
        # provide a `.database.command('ping')` target
        class _PingDB:
            def command(self, *a, **k):
                return {"ok": 1}

        self.database = _PingDB()

    def find(self, *a, **k):
        return self._coll.find(*a, **k)

    def aggregate(self, *a, **k):
        return self._coll.aggregate(*a, **k)

    def delete_many(self, *a, **k):
        return self._coll.delete_many(*a, **k)

    def bulk_write(self, *a, **k):
        return self._coll.bulk_write(*a, **k)


@pytest.fixture(scope="session")
def mongo_collection():
    client = mongomock.MongoClient()
    db = client["rolelens-db"]
    coll = db["jobs"]
    # ensure clean state
    coll.delete_many({})
    return _TestCollectionWrapper(coll)


@pytest.fixture
def client(mongo_collection):
    def _override_get_db():
        return mongo_collection

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()