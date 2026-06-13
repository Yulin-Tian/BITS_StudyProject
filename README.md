# Active Care Engine

The AI microservice for **Curastra** (AI-Augmented Personal Health Assistant,
Capstone Group 110). It does OCR + LLM work and is called over HTTP by the Node
main backend. It is **stateless** — it takes data in and returns JSON; it never
touches the database.

```
Android app  ->  Node main backend (port 3000)  ->  Active Care Engine (port 8000)
                                                     OCR + AI (this repo)
```

---

## 1. Requirements

- Python 3.12
- **Tesseract OCR** and **Poppler** installed (for image/scanned-PDF OCR).
  On Windows the paths go in `.env` (`TESSERACT_CMD`, `POPPLER_PATH`).
- An OpenAI API key (only needed when `SIMULATION_MODE=false`).

## 2. Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
copy .env.example .env            # then fill in the values
```

## 3. Run

```bash
uvicorn app.api_server:app --reload --port 8000
```

- Interactive docs:  http://localhost:8000/docs
- Health check:      http://localhost:8000/health

## 4. Environment variables (`.env`)

| Variable           | Purpose                                                        |
|--------------------|----------------------------------------------------------------|
| `OPENAI_API_KEY`   | OpenAI key (needed unless simulation mode is on)               |
| `OPENAI_MODEL`     | Model id (default `gpt-4o-mini`)                              |
| `TESSERACT_CMD`    | Path to `tesseract.exe` if not on PATH                        |
| `POPPLER_PATH`     | Path to poppler `bin` if not on PATH                         |
| `OCR_LANG`         | OCR language (default `eng`)                                  |
| `INTERNAL_API_KEY` | Shared secret. Node must send it in `X-Internal-Key`. **Empty = open (dev).** |
| `SIMULATION_MODE`  | `true` = AI endpoints return canned JSON, **no OpenAI calls** |

> **Production note:** on Railway, set these as platform env vars and ship **no**
> `.env` file (the app uses `load_dotenv(override=True)`, so a committed `.env`
> would shadow the platform vars). Keep `.env` gitignored — it already is.

## 5. Authentication

Every `/v1/*` endpoint requires the header **`X-Internal-Key: <INTERNAL_API_KEY>`**.
If `INTERNAL_API_KEY` is empty (local dev), the check is skipped so curl/Postman
work with no header. `/health` is always open.

## 6. Simulation / fallback mode

Set `SIMULATION_MODE=true` to make every AI endpoint return realistic canned
JSON **without calling OpenAI** — perfect for demos, when there's no key, and to
avoid cost while testing. Each AI response carries a `"simulated": true/false`
field. (This is the engine half of the agreed fallback strategy; Node wraps its
calls in try/catch for the other half.)

## 7. Endpoints

All bodies are JSON unless noted. All AI outputs include a `disclaimer`.

| Method | Path              | Purpose                                   |
|--------|-------------------|-------------------------------------------|
| GET    | `/health`         | Liveness check (open)                     |
| POST   | `/v1/extract`     | OCR/extract — **multipart** file upload   |
| POST   | `/v1/extract/url` | OCR/extract — **Cloudinary file_url** (use this from Node) |
| POST   | `/v1/generate`    | Care plan from verified text              |
| POST   | `/v1/simplify`    | Clinical instruction → plain language     |
| POST   | `/v1/lab-analyze` | Lab report → plain summary + flags        |
| POST   | `/v1/med-safety`  | Cross-medication duplicate/interaction alerts |
| POST   | `/v1/insights`    | Health insights from vitals/adherence     |
| POST   | `/v1/chat`        | AI health chatbot (context-aware)         |

### Request / response shapes

**`/v1/extract/url`**
```json
// req
{ "file_url": "https://res.cloudinary.com/.../prescription.jpg", "file_name": "prescription.jpg" }
// res
{ "file_name": "...", "extracted_text": "...", "ocr_used": true, "low_confidence": false }
```

**`/v1/simplify`**
```json
// req
{ "text": "Tab Augmentin 625mg PO BD x5/7 after food." }
// res
{ "simplified": "...", "tts_text": "...", "disclaimer": "...", "simulated": false }
```

**`/v1/lab-analyze`**
```json
// req
{ "verified_text": "Hemoglobin 11.2 g/dL (ref 13-17). ..." }
// res
{ "summary": "...", "flags": [ { "name": "Hemoglobin", "value": "11.2 g/dL", "status": "low", "note": "..." } ], "disclaimer": "...", "simulated": false }
```

**`/v1/med-safety`**
```json
// req
{ "medications": [ { "name": "Warfarin", "dosage": "5mg" }, { "name": "Aspirin", "dosage": "75mg" } ] }
// res
{ "alerts": [ { "type": "interaction", "medications": ["Warfarin","Aspirin"], "message": "...", "severity": "warning" } ], "disclaimer": "...", "simulated": false }
```

**`/v1/insights`**
```json
// req
{ "user_id": "u_123", "vitals_history": [ { "date": "2026-06-08", "bp": "122/80" } ], "adherence": [ { "medication": "Pan 40", "taken": 6, "scheduled": 7 } ] }
// res
{ "insights": [ { "title": "...", "detail": "...", "category": "trend" } ], "disclaimer": "...", "simulated": false }
```

**`/v1/chat`**
```json
// req
{ "user_id": "u_123", "message": "What is my Pan 40 for?", "context": { "medications": [...], "recent_vitals": [...], "active_care_plan": {...} } }
// res
{ "reply": "...", "used_context": true, "disclaimer": "...", "safety_flag": null, "simulated": false }
```
`safety_flag` is `"refused"` for diagnosis/treatment requests and
`"advised_see_doctor"` for possible emergencies; otherwise `null`.

### Errors

All failures return Node's convention with the right HTTP status:
```json
{ "error": "human readable message" }
```

## 8. Quick test (curl)

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/v1/simplify \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Tab Pan 40 OD before breakfast.\"}"
```

A ready-made **Postman collection** is in `postman_collection.json` — set the
`base_url` and `internal_key` variables and run any request. Hand this file to
the Node backend developer as the live contract.

## 9. Safety design (for the report)

- The engine never diagnoses, prescribes, or changes a dosage.
- Missing information triggers clarification questions, not guesses.
- Every AI output carries a disclaimer; care plans stay traceable to source text.
- The chatbot refuses diagnosis/treatment asks and escalates emergencies.
