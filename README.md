# 🎯 RoleLens

> **A containerized job market ETL and analytics platform built with FastAPI, MongoDB, Pandas, and Docker.**

<p align="center">

[![Docker CI](https://github.com/abdulrahmanm-in/rolelens/actions/workflows/ci.yml/badge.svg)](https://github.com/abdulrahmanm-in/rolelens/actions/workflows/ci.yml)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-7-47A248?logo=mongodb)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Engineering-150458?logo=pandas)
![Pytest](https://img.shields.io/badge/Pytest-Tests-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

</p>

---

## 🌐 Demo

| Service | Link |
|---------|------|
| API Docs | `https://external-lusa-rahmandev-d415ed9a.koyeb.app/docs` |
| ReDoc | `https://external-lusa-rahmandev-d415ed9a.koyeb.app/redoc` |

---

## 📌 Overview

RoleLens ingests technology job listings from Adzuna, transforms raw job data into analytics-ready records, stores them in MongoDB, and exposes job market insights through a FastAPI REST API.

This repository demonstrates full-stack backend engineering skills including ETL design, data modeling, scheduler integration, API development, Dockerization, and automated testing.

---

## 🚀 Features

- Automated Adzuna job ingestion for `Chennai` and `Bangalore`
- Daily ETL scheduling with APScheduler
- Manual ETL trigger endpoint
- Job deduplication by external ID
- Tech skill extraction from job descriptions
- Salary normalization and analytics aggregation
- MongoDB bulk upsert with 7-day rolling retention
- FastAPI REST API with OpenAPI docs
- Isolated tests using `mongomock`
- Dockerized local development environment

---

## 🛠️ Tech Stack

### Backend
- Python 3.11
- FastAPI
- Pandas
- Requests
- APScheduler

### Database
- MongoDB 7
- PyMongo

### Testing
- Pytest
- FastAPI TestClient
- mongomock

### DevOps
- Docker
- Docker Compose

---

## 🏗 Architecture

```mermaid
flowchart LR
  ADZ["Adzuna Jobs API"] --> ETL["ETL Pipeline<br/>(app/etl.py)"]
  SCHED["APScheduler<br/>Daily Trigger"] --> ETL
  MANUAL["Manual sync<br/>(/run-manual-sync)"] --> ETL
  ETL --> MONGO["MongoDB<br/>Jobs Collection"]
  MONGO --> API["FastAPI REST API<br/>(app/main.py)"]
  CLIENT["Clients / Swagger UI"] --> API
  
  style ADZ fill:#0288d1,color:#fff,stroke:#01579b,stroke-width:2px
  style ETL fill:#f57c00,color:#fff,stroke:#e65100,stroke-width:2px
  style MONGO fill:#c2185b,color:#fff,stroke:#880e4f,stroke-width:2px
  style API fill:#388e3c,color:#fff,stroke:#1b5e20,stroke-width:2px
  style CLIENT fill:#5e35b1,color:#fff,stroke:#311b92,stroke-width:2px
  style SCHED fill:#00838f,color:#fff,stroke:#004d40,stroke-width:2px
  style MANUAL fill:#d32f2f,color:#fff,stroke:#b71c1c,stroke-width:2px
```

- `app/etl.py` — performs extract, transform, and load operations
- `app/main.py` — exposes REST API and manages scheduler lifecycle
- `app/database.py` — configures MongoDB connection
- `tests/` — validates pipeline and API behavior


---

## 📂 Project Structure

```text
RoleLens/

├── app/
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── etl.py
│   ├── main.py
│   └── schemas.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_etl.py
│
├── docker-compose.yml
├── docker-compose.override.yml
├── docker-compose.prod.yml
├── docker-compose.test.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── pytest.ini
└── LICENSE
```

---

## 🔧 Installation

### Prerequisites

- Python 3.11
- Docker Desktop (recommended)
- MongoDB or Dockerized MongoDB instance

### Clone the repository

```bash
git clone https://github.com/abdulrahmanm-in/rolelens.git
cd RoleLens
```

### Create environment variables

```bash
copy .env.example .env
```

Update `.env` with your values:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
DATABASE_URL=mongodb://job_user:job_password@mongo:27017/rolelens_dev_db
```

---

## 🌐 Environment Variables

| Key | Description |
| --- | ----------- |
| `ADZUNA_APP_ID` | Adzuna API application ID |
| `ADZUNA_APP_KEY` | Adzuna API key |
| `DATABASE_URL` | MongoDB connection URI |

---

## ▶️ Run the Application

### Docker

```bash
docker compose up --build
```

### Local Python

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the API docs:

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Stop the app:

```bash
docker compose down
```

---

## 📡 API Endpoints

### General
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health` | Health and MongoDB status |

### Job Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/jobs/latest` | Latest ingested job postings |
| GET | `/trends` | Technology demand trends |
| GET | `/salaries` | Salary insights for a role |
| GET | `/run-manual-sync` | Trigger ETL pipeline manually |

### Query Parameters
- `role` — filter jobs by role or keyword
- `city` — filter jobs by city name
- `limit` — maximum number of jobs to return (1-100)

---

## 🧠 ETL Pipeline Details

1. Extracts IT jobs from Adzuna for `Chennai` and `Bangalore`.
2. Normalizes salary values and cleans job metadata.
3. Extracts technology keywords from job descriptions.
4. Deduplicates records using Adzuna job IDs.
5. Bulk upserts cleaned documents into MongoDB.
6. Removes job records older than 7 days.

---

## 🧪 Testing

Run tests locally:

```bash
pytest
```

Run tests in Docker:

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api
```

### What tests cover
- API endpoint behavior
- health check and response validation
- ETL transformation logic
- keyword extraction from descriptions
- duplicate job deduplication
- empty dataset handling

---

## 🔄 Continuous Integration

This repository is designed for CI validation with Docker and Pytest. The CI pipeline should verify:

- Docker image build
- ETL pipeline execution
- API endpoint validation
- Automated tests run successfully

---

## 🚀 Deployment

The application can be deployed using Docker Compose for production.

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## 🔐 Security & Reliability

- secure connection to MongoDB
- safe ETL execution with retries and error handling
- bulk upsert to prevent duplicate ingestion
- isolated test environment using `mongomock`
- clear environment variable configuration

---

## 🧭 Roadmap

### Planned Enhancements
- [ ] Add Adzuna pagination and incremental sync improvements
- [ ] Add data caching for faster analytics
- [ ] Add more advanced trend analysis endpoints
- [ ] Improve salary parsing and normalization
- [ ] Add historical analytics dashboards

---

## 🤝 Contributing

Contributions are welcome! Please follow standard GitHub PR workflow:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes with clear messages
4. Open a PR for review

---

## 📄 License

MIT License

---

## 👨‍💻 Author

**Abdul Rahman M**

- GitHub: https://github.com/abdulrahmanm-in
- LinkedIn: https://www.linkedin.com/in/abdul-rahman-m-660158206

---

## 📞 Support

For issues, questions, or suggestions:
- Open GitHub Issue: https://github.com/abdulrahmanm-in/RoleLens/issues
- Email: indmabdulrahman@gmail.com

**Happy coding! 🚀**
