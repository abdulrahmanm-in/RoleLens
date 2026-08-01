# 🎯 RoleLens

> **Production-ready Job Market Analytics Platform built with FastAPI, PostgreSQL, Pandas, Docker, and APScheduler.**

<p align="center">

[![Docker CI](https://github.com/abdulrahmanm-in/rolelens/actions/workflows/ci.yml/badge.svg)](https://github.com/abdulrahmanm-in/rolelens/actions/workflows/ci.yml)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Engineering-150458?logo=pandas)
![Pytest](https://img.shields.io/badge/Pytest-Passing-success?logo=pytest)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI-blue?logo=githubactions)
![License](https://img.shields.io/badge/License-MIT-yellow)

</p>

---

## 📌 Overview

RoleLens is a **containerized ETL and analytics platform** that continuously collects job listings from external APIs, transforms raw data into structured insights, stores the processed information in PostgreSQL, and exposes analytics through a RESTful API.

The project demonstrates real-world backend engineering practices including:

- Automated ETL pipelines
- REST API development
- Data cleaning & transformation
- Background job scheduling
- Analytics generation
- SQL database design
- Docker containerization
- Integration testing
- CI/CD automation

---

# ✨ Key Features

## 📥 Automated Data Ingestion

- Scheduled ETL pipeline using APScheduler
- Fetches latest job listings from external APIs
- Manual pipeline execution endpoint
- Incremental data synchronization

---

## 🧹 Data Processing Pipeline

Incoming job listings are automatically processed to:

- Remove duplicate jobs
- Normalize salary ranges
- Clean HTML from descriptions
- Standardize locations
- Extract technology keywords
- Prepare analytics-ready datasets

---

## 📊 Job Market Analytics

RoleLens provides insights including:

- Technology demand trends
- Average salary insights
- Recently posted jobs
- Skill frequency analysis
- Job market statistics

---

## ⚡ REST API

Built with FastAPI and automatically documented using OpenAPI.

Available endpoints include:

| Endpoint | Description |
|----------|-------------|
| `GET /` | API Home |
| `GET /health` | System health & database connectivity |
| `GET /jobs/latest` | Fetch latest job postings |
| `GET /trends` | Technology demand analytics |
| `GET /salaries` | Salary insights by role |
| `GET /run-manual-sync` | Trigger ETL pipeline manually |

---

# 🏗 System Architecture

```text
                 External Job APIs
                        │
                        ▼
              Automated ETL Scheduler
                 (APScheduler)
                        │
                        ▼
             Data Processing Pipeline
        ┌─────────────────────────────┐
        │ Pandas                      │
        │ • Clean Data                │
        │ • Normalize Salaries        │
        │ • Remove Duplicates         │
        │ • Extract Tech Skills       │
        └─────────────────────────────┘
                        │
                        ▼
              PostgreSQL Database
                        │
                        ▼
                 FastAPI REST API
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
   Swagger UI                    External Clients
```

---

# 🛠 Tech Stack

## Backend

- Python 3.11
- FastAPI
- SQLAlchemy
- APScheduler

### Data Engineering

- Pandas
- NumPy
- Regex Processing

### Database

- PostgreSQL 17

### DevOps

- Docker
- Docker Compose
- GitHub Actions

### Testing

- Pytest
- FastAPI TestClient
- PostgreSQL Integration Tests

---

# 📂 Project Structure

```text
rolelens/

├── app/
│   ├── database.py
│   ├── dependencies.py
│   ├── etl.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_etl.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docker-compose.yml
├── docker-compose.override.yml
├── docker-compose.test.yml
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

---

# 🚀 Quick Start

Clone the repository

```bash
git clone https://github.com/abdulrahmanm-in/rolelens.git

cd rolelens
```

Create environment variables

```bash
cp .env.example .env
```

Example:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key

DATABASE_URL=postgresql://job_user:job_password@postgres:5432/rolelens_dev_db
TEST_DATABASE_URL=postgresql://job_user:job_password@postgres:5432/rolelens_test_db
```

Build and start the application

```bash
docker compose up --build
```

Stop the application

```bash
docker compose down
```

---

# 📖 API Documentation

Once running:

| Documentation | URL |
|--------------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

# 📡 API Endpoints

## Health Monitoring

```http
GET /health
```

Returns API health, database connectivity, and timestamp.

Example

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-08-01T15:00:00Z"
}
```

---

## Latest Jobs

```http
GET /jobs/latest?limit=10
```

Returns the latest ingested job postings.

Example

```json
[
  {
    "title": "Backend Developer",
    "company": "ABC Technologies",
    "location": "Chennai",
    "salary_min": 1200000,
    "salary_max": 1800000,
    "tech_stack": "Python, Docker, PostgreSQL"
  }
]
```

---

## Technology Trends

```http
GET /trends
```

Returns aggregated technology demand metrics.

---

## Salary Insights

```http
GET /salaries?role=data engineer
```

Returns average minimum and maximum salaries for a specified role.

---

## Manual ETL Execution

```http
GET /run-manual-sync
```

Triggers immediate execution of the ingestion pipeline.

---

# 🧪 Testing

Run the complete test suite inside Docker.

```bash
docker compose \
-f docker-compose.yml \
-f docker-compose.test.yml \
run --rm api
```

Cleanup

```bash
docker compose \
-f docker-compose.yml \
-f docker-compose.test.yml \
down -v
```

Testing includes:

- API endpoint validation
- ETL pipeline testing
- Database integration
- SQLAlchemy ORM testing
- Analytics validation

---

# 🔄 Continuous Integration

Every push and pull request automatically performs:

```text
Push / Pull Request
        │
        ▼
Flake8 Linting
        │
        ▼
Docker Build
        │
        ▼
Pytest Execution
        │
        ▼
Production Image Verification
```

---

# 💡 Skills Demonstrated

This project showcases practical experience with:

- Python Backend Development
- REST API Design
- FastAPI
- SQLAlchemy ORM
- PostgreSQL
- Data Engineering
- ETL Pipelines
- Data Analytics
- Pandas
- Docker
- Docker Compose
- Background Scheduling
- Automated Testing
- GitHub Actions
- CI/CD
- Clean Architecture
- Containerized Development

---

# 🚀 Future Enhancements

- Authentication & Authorization
- Redis Caching
- Historical Trend Dashboard
- Grafana Monitoring
- Elasticsearch Search
- Kubernetes Deployment
- AWS Cloud Deployment
- Machine Learning Based Salary Prediction

---

# 📄 License

Distributed under the MIT License.

---

# 👨‍💻 Author

**Abdul Rahman M**

- GitHub: https://github.com/abdulrahmanm-in
- LinkedIn: https://www.linkedin.com/in/abdul-rahman-m-660158206