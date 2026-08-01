import pandas as pd
from app.etl import transform_data


def test_transform_data_empty():
    """Ensure transform logic handles empty raw inputs safely."""
    df = transform_data([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_transform_data_keyword_extraction():
    """Verify skill parsing extracts keywords correctly from descriptions."""
    raw_mock_payload = [
        {
            "id": "job_123",
            "title": "Senior Data Engineer",
            "company": {"display_name": "Acme Corp"},
            "location": {"display_name": "Chennai, India"},
            "description": "Requires strong Python, SQL, AWS, and FastAPI skills.",
            "salary_min": 600000,
            "salary_max": 1200000,
            "redirect_url": "https://example.com/job/123"
        }
    ]

    df = transform_data(raw_mock_payload)

    assert not df.empty
    assert len(df) == 1
    tech_stack = df.iloc[0]["tech_stack"]
    assert "python" in tech_stack
    assert "sql" in tech_stack
    assert "aws" in tech_stack
    assert "fastapi" in tech_stack
    assert df.iloc[0]["company"] == "Acme Corp"


def test_transform_data_deduplication():
    """Verify duplicate job IDs are dropped during transformation."""
    raw_mock_payload = [
        {"id": "job_999", "title": "DE Role 1", "description": "Python"},
        {"id": "job_999", "title": "DE Role 1 Duplicate", "description": "Python"}
    ]

    df = transform_data(raw_mock_payload)
    assert len(df) == 1  # 1 duplicate dropped