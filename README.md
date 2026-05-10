# MarketGrid — Full-Stack E‑Commerce (DBMS Lab)

Production-style prototype: **FastAPI + PostgreSQL + MongoDB + Alembic**, **React + Vite + Tailwind**, **JWT RBAC**, **SQL triggers/views**, **transactional checkout**, and **Mongo-backed activity logs**.

## Quick start (Docker)

```bash
cd ecommerce-dbms
docker compose up --build
```

| Service    | URL                         |
|-----------|-----------------------------|
| Frontend  | http://localhost:5173       |
| API       | http://localhost:8000       |
| API docs  | http://localhost:8000/docs  |
| Postgres  | localhost:5432              |
| MongoDB   | localhost:27017             |

**Seeded accounts** (from `scripts/seed.py`):

- `admin@example.com` / `Admin123!`
- `seller@example.com` / `Seller123!`
- `buyer@example.com` / `Buyer123!`

Coupon for checkout: **SAVE10** (10% off).

---

## Local development (without Docker frontend)

**Backend**

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
# Requires PostgreSQL client libs; `psycopg2-binary` is in requirements.txt
copy .env.example .env     # adjust DATABASE_URL / MONGO_URI as needed
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd frontend
npm install
set VITE_API_URL=http://localhost:8000/api   # Windows cmd
npm run dev
```

---

## What this demonstrates

- **PostgreSQL**: normalized schema, PK/FK/CHECK/UNIQUE, indexes, joins, aggregates, nested subqueries (admin dashboard revenue), **`SELECT … FOR UPDATE`** in checkout for oversell prevention inside a transaction.
- **Triggers** (applied in Alembic): inventory decrement on `order_items` insert; low-stock seller notification on `inventory` update; order confirmation when `payments.status` becomes `completed`; **`BEFORE DELETE` audit** row on products.
- **Views**: `v_top_selling_products`, `v_monthly_sales`, `v_active_customers`; SQL function `fn_order_item_subtotal`.
- **MongoDB**: append-only / flexible collections for `product_view_logs`, `recommendation_logs`, `user_activity_logs`, `notification_logs`, `chat_support_messages`, `audit_logs` — see `docs/DATABASE.md` for rationale.
- **RBAC**: roles `admin`, `seller`, `customer`; FastAPI dependencies guard `/api/admin/*` and `/api/seller/*`.

---

## Project layout

```
ecommerce-dbms/
  backend/           # FastAPI app, Alembic, SQLAlchemy models, triggers SQL
  frontend/          # Vite React SPA
  docs/              # ER, normalization, concurrency, Mongo justification
  docker-compose.yml
```

---

## API surface (prefix `/api`)

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET /categories/`, `GET /products/`, `GET /products/{id}`, `POST /products/seller`
- `GET|POST /cart/`, `DELETE /cart/`
- `GET|POST /addresses/`, `DELETE /addresses/{id}`
- `POST /orders/checkout`, `GET /orders/mine`
- `GET|POST /wishlist/`, `DELETE /wishlist/{product_id}`
- `GET|POST /reviews/product/{product_id}`
- `GET /notifications/`, `POST /notifications/mark-all-read`
- `POST /support/` (Mongo log)
- `GET /recommendations/`
- **Admin** (`admin` role): `/admin/analytics/*`, `/admin/users`, `/admin/products/*`, `/admin/audit/sql`, …
- **Seller** (`seller` role): `/seller/orders`, `/seller/analytics/sales`, `PATCH /seller/products/{id}`

Open **http://localhost:8000/docs** for the interactive OpenAPI UI.

---

## Documentation

- [docs/DATABASE.md](docs/DATABASE.md) — ER (Mermaid), normalization, triggers, transactions, concurrency, Mongo vs SQL, conceptual `GRANT` notes.

---

## License

Educational / demonstration use.
