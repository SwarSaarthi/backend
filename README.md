# SwarSaarthi — FastAPI Backend

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql+asyncpg://user:password@your-neon-host/dbname?sslmode=require
JWT_SECRET=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Seed Database

```bash
python -m app.db.init_db
```
