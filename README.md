# Prescription Extraction & Matching System

A production-ready backend for extracting structured data from medical prescriptions (printed or handwritten) and matching them against BMDC (doctors) and DGDA (medicines) databases.

## Technology Stack
- **Backend:** FastAPI, Python 3.11+
- **Database:** PostgreSQL 16 with `pgvector` and `pg_trgm`
- **VLM:** Qwen2.5-VL-7B (served via vLLM)
- **Fallback:** OpenAI GPT-4o Vision
- **Job Orchestration:** FastAPI BackgroundTasks (extensible to Celery)
- **Embeddings:** Local (`intfloat/multilingual-e5-base`), Gemini, or Jina AI

---

## Prerequisites
- Docker & Docker Compose
- NVIDIA GPU with 24GB+ VRAM (for local vLLM)
- Python 3.11 (for local development)

---

## Setup Instructions

### 1. Environment Configuration
Copy the template and fill in your API keys:
```bash
cp .env.example .env
```

### 2. Run locally
```bash
uv sync
uv run uvicorn app.main:app --reload
```

---

## Seeding Databases

Place your CSV data in `db/seed/data/*.csv` then run:

### Seed Doctors (BMDC)
```bash
python db/seed/seed_doctors.py db/seed/data/bmdc_doctors.csv
```

### Seed Medicines (DGDA)
```bash
python db/seed/seed_medicines.py db/seed/data/dgda_medicines.csv
```

---

## Usage Example

### Submit a Prescription
```bash
curl -X POST "http://localhost:8000/api/v1/prescriptions/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/prescription.jpg" \
  -F "priority=normal"
```

### Get Results
```bash
curl "http://localhost:8000/api/v1/prescriptions/{id}"
```

---

## Configuration Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Postgres Async Connection String | Required |
| `VLLM_BASE_URL` | Endpoint for the VLM service | `http://localhost:8001/v1` |
| `EMBEDDING_PROVIDER` | `local`, `gemini`, or `jina` | `local` |
| `CLOUD_FALLBACK_THRESHOLD` | Confidence score to trigger GPT-4o | `0.70` |
| `HUMAN_REVIEW_THRESHOLD` | Score below which human review is flagged | `0.60` |

---

## Project Structure
- `app/core/`: Layered logic (Preprocessing, Extraction, Normalization, Pipeline)
- `app/services/`: External integrations (VLM, Matching, Embeddings)
- `app/models/`: SQLAlchemy and Pydantic data models
- `db/seed/`: Data ingestion scripts
