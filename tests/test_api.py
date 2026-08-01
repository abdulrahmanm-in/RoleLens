def test_home_endpoint(client):
    """Verify root endpoint responds with OpenAPI welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check(client):
    """Verify system health endpoint validates database connection."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "database" in data


def test_get_latest_jobs_empty(client):
    """Verify /jobs/latest returns a clean empty list when DB has no rows."""
    response = client.get("/jobs/latest")
    assert response.status_code == 200
    assert response.json() == []


def test_get_tech_trends_empty(client):
    """Verify /trends endpoint handles empty records gracefully."""
    response = client.get("/trends")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"] == []


def test_get_salary_insights_empty(client):
    """Verify /salaries endpoint returns N/A for roles without salary data."""
    response = client.get("/salaries?role=data%20engineer")
    assert response.status_code == 200
    data = response.json()
    assert data["avg_min_salary"] == "N/A"
    assert data["avg_max_salary"] == "N/A"