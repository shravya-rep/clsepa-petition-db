# CLSEPA Petition Decision Database

A secure, searchable database of tenant petition decisions for [Community Legal Services in East Palo Alto](https://www.clsepa.org). Enables tenants to search past rent adjustment and habitability rulings from East Palo Alto and Mountain View to inform their own petitions.

## Features

- **Public search** — Filter decisions by issue category, city, decision type, date, case number, or address
- **PDF access** — View full decision documents directly from search results
- **Admin panel** — Upload new decisions, assign keyword tags, manage entries (no technical knowledge required)
- **Keyword tagging** — Decisions tagged with categories from CLSEPA's petition intake form (mold, plumbing, electrical, heat, rent overcharge, etc.)
- **Audit logging** — All admin actions tracked with user and timestamp
- **Role-based access** — JWT authentication separating public (read-only) and admin (upload/manage) access

## Tech Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL |
| Backend API | FastAPI (Python) |
| Frontend | React + Tailwind CSS |
| Authentication | JWT with bcrypt |
| PDF Extraction | pdfplumber (deterministic) |
| Hosting | Railway |

## Project Structure

```
clsepa-petition-db/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes (auth, decisions, keywords, pdfs, audit)
│   │   ├── core/         # Config, database, security
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # PDF extraction pipeline
│   ├── tests/            # 35 tests (pytest)
│   ├── alembic/          # Database migrations
│   ├── migrate_decisions.py  # Bulk PDF migration script
│   └── seed_admin.py     # Initial admin user setup
├── frontend/
│   └── src/
│       ├── pages/        # SearchPage, DecisionPage, LoginPage, AdminPage
│       ├── components/   # Navbar
│       ├── context/      # AuthContext
│       └── api/          # API client + types
└── invoices/             # Per-phase invoices
```

## Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL

### Backend

```bash
cd backend
cp .env.example .env  # Edit with your database credentials
pip install -r requirements.txt
alembic upgrade head
python seed_admin.py   # Create first admin user
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key (use a strong random string) |
| `PDF_UPLOAD_DIR` | Directory for uploaded PDFs (default: `uploads/pdfs`) |
| `VITE_API_URL` | Backend API URL (frontend, default: `http://localhost:8000`) |

## Data Migration

To import existing decision PDFs:

```bash
cd backend
python migrate_decisions.py /path/to/given/directory
```

This processes PDFs from `Mountain View/` and `East Palo Alto/` subdirectories:
- **Mountain View**: Automatic extraction from structured tables (high confidence)
- **East Palo Alto**: Filename parsing only (scanned images require manual metadata entry)

## API Endpoints

### Public
- `GET /api/decisions/` — Search decisions (query params: keyword, city, decision_type, date_from, date_to, q)
- `GET /api/decisions/{id}` — Get single decision
- `GET /api/pdfs/{id}` — Download/view decision PDF
- `GET /api/keywords/` — List all keyword categories

### Admin (requires JWT)
- `POST /api/auth/login` — Login
- `POST /api/decisions/` — Upload new decision (multipart: PDF + JSON metadata)
- `PUT /api/decisions/{id}` — Edit decision metadata
- `DELETE /api/decisions/{id}` — Delete decision
- `POST /api/keywords/` — Add keyword category
- `DELETE /api/keywords/{id}` — Remove keyword category
- `POST /api/auth/register` — Register new admin user
- `GET /api/audit/` — View audit log

## Testing

```bash
cd backend
pytest tests/ -v
```

35 tests covering auth, CRUD, search/filtering, and PDF extraction.

## Deployment (Railway)

1. Create a Railway project and add a PostgreSQL database
2. Set environment variables (DATABASE_URL, SECRET_KEY)
3. Deploy backend from the `backend/` directory
4. Deploy frontend from the `frontend/` directory (set VITE_API_URL to backend URL)
5. Run `alembic upgrade head` and `python seed_admin.py` on first deploy

## Staff Guide

### Uploading a New Decision
1. Log in at `/login` with your admin credentials
2. Go to **Admin** > **Upload Decision**
3. Select the PDF file
4. Fill in: City, Case Number, Address, Decision Date, Hearing Officer
5. Click the keyword tags that apply (e.g., Mold, Plumbing, Heat)
6. Click **Upload Decision**

### Managing Keywords
1. Go to **Admin** > **Keywords** tab
2. Type a new keyword and click **Add**
3. Click **x** next to a keyword to remove it

## License

All deliverables are property of CLSEPA per contract terms.
