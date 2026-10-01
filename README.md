# MK Construction & Builders API

Production FastAPI backend for the Construction Quotation & Estimation Management System.

## Stack

- Python 3.11+
- FastAPI
- MySQL 8
- SQLAlchemy 2 async (`aiomysql`)
- Alembic
- JWT auth + RBAC

## Local setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Update `.env` with a real `DATABASE_URL` and `JWT_SECRET_KEY`.

```bash
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

## Seed users

| Role | Email | Password |
| --- | --- | --- |
| ADMIN | admin@mkconstruction.in | Admin@12345 |
| MANAGER | manager@mkconstruction.in | Manager@12345 |
| ESTIMATOR | estimator@mkconstruction.in | Estimator@12345 |
| VIEWER | viewer@mkconstruction.in | Viewer@12345 |

Change these immediately in production.

## Production

```bash
gunicorn -c gunicorn.conf.py app.main:app
```

## Docker

```bash
docker compose up --build
```

Then run migrations and seed against the MySQL container.

## Tests

```bash
pytest
```

Calculation tests cover the reference example:

- 2000 × 900 = ₹18,00,000
- 2000 × 700 = ₹14,00,000
- 5% discount and 18% GST → grand total ₹35,87,200
