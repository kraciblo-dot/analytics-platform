# 📊 Multi-Tenant Analytics Platform

A production-grade, multi-tenant analytics dashboard built with Next.js and FastAPI. This platform allows organizations to ingest event data via CSV, process it asynchronously, and visualize it on a fully customizable, drag-and-drop interactive dashboard.

## 🚀 Tech Stack

**Frontend:**
* **Framework:** Next.js (React 19, Turbopack)
* **State Management:** Zustand (Global Auth State)
* **Data Fetching:** Axios (with smart Interceptors)
* **Visualization:** Recharts
* **Interactive UI:** React-Grid-Layout (Drag-and-Drop), Tailwind CSS, Lucide Icons

**Backend:**
* **Framework:** FastAPI (Python)
* **Background Processing:** Celery
* **Database:** PostgreSQL (SQLAlchemy ORM)
* **Message Broker:** Redis
* **Authentication:** JWT (JSON Web Tokens) with RBAC Dependency Injection

---

## ✨ Key Features & Architectural Upgrades

### 1. Interactive Drag-and-Drop Dashboard
* **React Grid Layout Integration:** Implemented a responsive 12-column grid system using modern React hooks (`useContainerWidth`) to bypass legacy higher-order component limitations.
* **Widget Customization:** Users can drag widgets by their headers and resize them.
* **Layout Persistence:** Dashboard layouts (X, Y, Width, Height) are saved directly to the database and reloaded upon login.
* **Dynamic Time-Series Charting:** Recharts graphs dynamically update based on user-selected event types (`page_view`, `button_click`, etc.) and time ranges (Last 7, 14, 30, 90 days).

### 2. Strict Multi-Tenancy & Data Isolation
* **Zustand + JWT Auth:** Upon login, JWT payloads are decoded to extract the `role` and `org_id`, which are stored securely in memory via Zustand.
* **Axios Interceptors:** All outgoing requests automatically attach the Authorization bearer token.
* **Backend Dependency Injection:** FastAPI endpoints extract `current_user.organization_id` from the token and append it to all database queries, ensuring absolute data isolation between organizations.

### 3. Asynchronous Data Ingestion (Celery)
* **Raw File Processing:** Moved away from fragile frontend CSV parsing (`PapaParse`). The frontend now sends raw `multipart/form-data` directly to the backend.
* **Non-Blocking Architecture:** FastAPI receives the CSV and immediately offloads the parsing and database insertion to a **Celery Background Worker** via Redis. This prevents API timeouts on massive dataset uploads.
* **Organization Tagging:** Celery tasks are explicitly passed the `org_id` to ensure newly ingested historical data is strictly bound to the uploading organization.

---

## 🔄 System Data Flows

### Authentication Flow
1. User submits credentials via the UI.
2. FastAPI validates credentials and returns a signed JWT.
3. Frontend decodes the JWT (extracting `org_id`) and stores it in Zustand.
4. User is routed to the Dashboard.

### Background Data Ingestion Flow
1. User drops a CSV file into the `/import` dropzone.
2. Axios POSTs raw `FormData` to `/api/events/upload-csv`.
3. FastAPI validates the file type, accepts it (Returns `202 Accepted` to UI), and calls `process_event_async.delay(file_data, org_id)`.
4. Celery worker picks up the task from the Redis queue.
5. Worker parses the CSV, normalizes timestamps/properties, and bulk inserts them into PostgreSQL tagged with the `org_id`.

### Interactive Analytics Flow
1. User selects "Button Clicks" and "Last 30 Days" from the dashboard dropdowns.
2. Frontend triggers `GET /api/analytics/timeseries?event_name=button_click&days_back=30`.
3. FastAPI intercepts the request, verifies the JWT, and extracts the `org_id`.
4. SQLAlchemy queries the database: `WHERE organization_id = :org_id AND event_name = 'button_click' AND timestamp >= :date`.
5. Backend calculates daily aggregates and true `COUNT(DISTINCT user_id)` for unique visitors.
6. JSON response updates the Recharts widget and KPI cards seamlessly.

---

## ☁️ Deployment Architecture

This application is designed to be deployed across a distributed microservice environment.

**Frontend (Vercel):**
* Requires `NEXT_PUBLIC_API_URL` pointing to the backend Web Service URL.

**Backend (Render):**
* **Web Service:** Runs `uvicorn app.main:app`. Handles HTTP traffic and API routing.
* **Background Worker:** Runs `celery -A app.tasks.event_tasks worker`. Handles asynchronous CSV processing.
* **Managed Redis:** Acts as the message broker between FastAPI and Celery.
* **Managed PostgreSQL:** The primary persistent data store.

*Backend Environment Variables Required:*
* `DATABASE_URL` (Internal DB URL)
* `REDIS_URL` (Internal Redis URL)
* `CORS_ORIGINS` (Frontend URL whitelist)
* `SECRET_KEY` (For JWT generation)

---

## 🧪 Next Steps: Testing Strategy
The next phase of this project involves rigorous End-to-End (E2E) and Integration testing, focusing on:
1. Validating JWT token expiration and Zustand state clearing.
2. Asserting data isolation (User A cannot query Organization B's events).
3. Validating Celery worker fallback behavior for malformed CSV payloads.