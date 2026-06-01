# WebGuard Pro — Backend Setup Guide

## Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

---

## Step 1 — Create Virtual Environment

```bash
cd webguard-backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

---

## Step 2 — Install Dependencies

```bash
# Development
pip install -r requirements-dev.txt

# OR Production only
pip install -r requirements.txt
```

---

## Step 3 — Configure Environment Variables

```bash
copy .env.example .env
```

Edit `.env` with your values:
```
SECRET_KEY=your-very-long-random-secret-key
DB_NAME=webguard_db
DB_USER=webguard_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

---

## Step 4 — Create PostgreSQL Database

```sql
-- Run in psql
CREATE DATABASE webguard_db;
CREATE USER webguard_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE webguard_db TO webguard_user;
ALTER USER webguard_user CREATEDB;  -- needed for test DB
```

---

## Step 5 — Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

Expected output:
```
Applying users.0001_initial... OK
Applying token_blacklist.0001_initial... OK
... (all migrations OK)
```

---

## Step 6 — Create Superuser

```bash
python manage.py createsuperuser
# Enter: email, full_name, password
```

---

## Step 7 — Run Django Development Server

```bash
python manage.py runserver
```

Visit: http://localhost:8000/admin/
Visit: http://localhost:8000/health/

---

## Step 8 — Run Celery Worker (separate terminal)

```bash
# Activate venv first
celery -A webguard worker -l info -Q default,scans,dast,reports
```

---

## Step 9 — Run Celery Beat (separate terminal)

```bash
celery -A webguard beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---


```
