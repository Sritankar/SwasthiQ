# SwasthiQ Pharmacy Module Assignment

Full-stack implementation of the Pharmacy Hiring Assignment with:

- `backend/`: Python FastAPI REST API with SQLite
- `frontend/`: React + Vite UI (hooks, reusable components, real API calls)
- `README.md`: Setup, API contracts, and consistency rules

## Implemented Pages

1. Dashboard page (sales overview)
2. Inventory page (table + filters + add/update + status actions)
3. Medicine detail page (status transitions and full medicine metadata)

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic, SQLite
- Frontend: React (functional components + hooks), React Router, Vite

## Project Structure

```text
api/
  index.py
backend/
  app/
    main.py
    database.py
    models.py
    schemas.py
    services.py
    seed.py
    routers/
      dashboard.py
      inventory.py
  requirements.txt
frontend/
  src/
    api/
    components/
    pages/
    utils/
  package.json
Dockerfile
render.yaml
requirements.txt
vercel.json
```

## Run Locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

If needed, set API base URL:

```bash
set VITE_API_BASE_URL=http://localhost:8000/api
```

## Deploy to Render (Single URL for Frontend + Backend)

This repo supports one Render web service using Docker:

1. Frontend is built in Docker and served by FastAPI at `/`
2. Backend APIs run at `/api/*` on the same domain

### Option A: Blueprint deploy (`render.yaml`)

1. Push this repo to GitHub.
2. In Render dashboard, choose **New** -> **Blueprint**.
3. Select this repo and deploy.
4. Render creates:
   - Web service: `flow-swasthiq`
   - Postgres database: `flow-swasthiq-db`
5. Set `ALLOWED_ORIGINS` in the web service environment to your Render app URL:
   - `https://<your-render-service>.onrender.com`
6. Redeploy the web service.

### Option B: Manual deploy

1. In Render dashboard, create **PostgreSQL** service.
2. Create **Web Service** from this repo with:
   - Runtime: `Docker`
   - Dockerfile Path: `./Dockerfile`
3. Add environment variables in the web service:
   - `DATABASE_URL` = Render Postgres Internal/External connection string
   - `ALLOWED_ORIGINS` = `https://<your-render-service>.onrender.com`
4. Deploy.

### Verify

1. Open `https://<your-render-service>.onrender.com`
2. Check health endpoint:
   - `https://<your-render-service>.onrender.com/api/health`

### Notes

1. `frontend/src/api/client.js` already uses `/api` in production, so frontend and backend stay connected on one domain.
2. Do not use SQLite on Render production unless you attach a persistent disk.

## API Contracts

All APIs return structured JSON:

```json
{
  "success": true,
  "data": {}
}
```

### Dashboard APIs

- `GET /api/dashboard/sales-summary?target_date=YYYY-MM-DD`
  - Returns today's sales revenue, transaction count, average order value
- `GET /api/dashboard/items-sold?target_date=YYYY-MM-DD`
  - Returns total quantity sold for date
- `GET /api/dashboard/low-stock?limit=10`
  - Returns low/out-of-stock medicines
- `GET /api/dashboard/purchase-orders`
  - Returns purchase order summary (pending/completed/cancelled + value)
- `GET /api/dashboard/recent-sales?limit=10`
  - Returns recent sales list for dashboard table

### Inventory APIs

- `GET /api/inventory/summary`
  - Returns inventory counts by status + stock units + inventory valuation
- `GET /api/inventory/medicines`
  - Query params supported:
    - `q` (search by name/category/generic/manufacturer/batch)
    - `category`
    - `status` (`active`, `low_stock`, `expired`, `out_of_stock`)
    - `low_stock` (`true/false`)
    - `expired` (`true/false`)
    - `out_of_stock` (`true/false`)
    - `page`, `page_size`
- `GET /api/inventory/medicines/{medicine_id}`
  - Returns medicine details
- `POST /api/inventory/medicines`
  - Adds a medicine with validation
- `PUT /api/inventory/medicines/{medicine_id}`
  - Updates medicine fields and recomputes status
- `PATCH /api/inventory/medicines/{medicine_id}/status`
  - Explicitly marks status (`active`, `low_stock`, `expired`, `out_of_stock`)
- `GET /api/inventory/categories`
  - Returns distinct categories for filters

### Patient Sale APIs

- `POST /api/patient-sales`
  - Records medicine sale for a patient
  - Required fields: `patient_id`, `medicine_id`, `quantity`
  - Optional fields: `patient_name`, `dosage_instructions`, `notes`
  - Also updates stock and medicine status consistently
- `GET /api/patient-sales`
  - Lists patient medicine sale records
  - Query params: `q`, `patient_id`, `medicine_id`, `page`, `page_size`
- `GET /api/patient-sales/patients/{patient_id}/records`
  - Fetches medicine sale records by patient id

## Validation and Error Handling

- Pydantic request models validate types, ranges, and required fields
- Duplicate batch numbers return `409 Conflict`
- Missing resources return `404 Not Found`
- Empty update payload returns `400 Bad Request`

## Data Consistency Rules on Update

Status is always recomputed using business rules:

1. Expired if `expiry_date < today`
2. Out of stock if `stock_quantity <= 0`
3. Low stock if `stock_quantity <= reorder_level`
4. Otherwise active

When status is manually marked:

- Mark `expired` forces expiry date into past if needed
- Mark `out_of_stock` forces stock to zero
- Mark `low_stock` keeps stock at or below reorder threshold
- Mark `active` normalizes values to satisfy active conditions

This ensures a medicine record is never left in a contradictory state after edits.
