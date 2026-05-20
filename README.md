# Liblit Backend

FastAPI backend for USA Ghost Writer contact requests.

## Setup

1) Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2) Create `.env` from the example:

```bash
copy .env.example .env
```

3) Run the server:

```bash
uvicorn app.main:app --reload --port 8000
```

### Production uploads

Portfolio cover images are now stored in the database and served through `/api/portfolio/{item_id}/cover-image`, so production does not need a writable filesystem for uploads.

## Endpoint

- POST `http://127.0.0.1:8000/api/contact`

Payload:

```json
{
  "name": "Jane Doe",
  "phone": "+1 555 222 3333",
  "email": "jane@example.com",
  "service": "Ghostwriting",
  "message": "I need help with a memoir",
  "context": "contact",
  "sms_consent": true
}
```
