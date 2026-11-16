# SwarSaarthi — FastAPI Backend

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the `backend/` directory. Generate a signing secret with
`python -c "import secrets; print(secrets.token_urlsafe(48))"` and paste the result
as `JWT_SECRET`. The server refuses to start with a missing, short, or former
built-in secret. Keep this value private and stable across restarts and workers.

```env
DATABASE_URL=sqlite+aiosqlite:///./swarsaarthi.db
JWT_SECRET=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

For PostgreSQL, set `DATABASE_URL` to
`postgresql+asyncpg://user:password@your-neon-host/dbname?ssl=require`.
The requirements include both database drivers and PyAV (`av`) for browser-audio
conversion. Configure `HF_TOKEN` if needed for model access, and optionally
`SWAR_GOOGLE_KEY` / `GROQ_API_KEY` for online coaching.

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Use `python -m uvicorn` with the environment's interpreter instead of a bare
`uvicorn` command: a globally installed executable can bypass the activated environment.
PowerShell users can also run `.\run.ps1`; it selects the project interpreter
and working directory automatically. Use `.\run.ps1 -NoReload` for a single server process.

The primary speech model is loaded on startup; its first download requires internet
access. Whisper is downloaded only if fallback transcription is needed. Audio
resampling uses PyAV, and decoding uses the plain Wav2Vec2 processor; no separate
TorchAudio or language-model decoder installation is required.

## Seed Database

```bash
.\.venv\Scripts\python.exe -m app.db.init_db
```

This creates tables and seeds both words and sentences in `DATABASE_URL`.
It can be run again without duplicating the dataset. To seed only sentences,
run `python -m app.db.seed_sentences` from the backend directory.

## Regression Tests

```bash
python -m unittest discover -s tests -v
```

These tests validate signing-secret configuration and dataset initialization using
in-memory SQLite databases. They do not use your database or download speech models.
