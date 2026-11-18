<div align="center">

<img src="./docs/images/marketgrid-logo.svg" alt="MarketGrid logo" width="120"/>

# MarketGrid

**A multi-role e-commerce backend built to be correct under concurrency, decoupled through messaging, and run on Kubernetes.**

[![CI](https://github.com/Anantha-Shayan/ecommerce/actions/workflows/ci.yml/badge.svg)](https://github.com/Anantha-Shayan/ecommerce/actions/workflows/ci.yml)
[![CD](https://github.com/Anantha-Shayan/ecommerce/actions/workflows/cd.yml/badge.svg)](https://github.com/Anantha-Shayan/ecommerce/actions/workflows/cd.yml)
![Last commit](https://img.shields.io/github/last-commit/Anantha-Shayan/ecommerce?style=flat)

![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-6BA81E?style=flat)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?style=flat&logo=postgresql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB_7-47A248?style=flat&logo=mongodb&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ_3.13-FF6600?style=flat&logo=rabbitmq&logoColor=white)
<br/>
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![NGINX](https://img.shields.io/badge/NGINX_Ingress-009639?style=flat&logo=nginx&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=githubactions&logoColor=white)
![GHCR](https://img.shields.io/badge/GHCR-181717?style=flat&logo=github&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat&logo=googlecloud&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=flat&logo=grafana&logoColor=white)
<br/>
![React](https://img.shields.io/badge/React_18-20232A?style=flat&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat&logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white)

[Architecture](#architecture) · [Engineering decisions](#engineering-decisions) · [Quick start](#quick-start) · [Kubernetes](#deploying-to-kubernetes-minikube) · [Roadmap](#roadmap)

</div>

---

## Overview

MarketGrid is an e-commerce platform with three roles (buyers, sellers and admins) and the backend work a real store needs: a checkout that cannot oversell stock, payment-triggered notifications that never block a request, and an operations story that goes from a single VM to a Kubernetes cluster.

The project grew in stages, and each stage is still in the repo:

1. **Data layer first.** A normalized PostgreSQL schema (21 tables) that enforces business rules with constraints, PL/pgSQL triggers, views and an audit log, all versioned through Alembic.
2. **Docker Compose on GCP.** GitHub Actions builds images, tags them with the commit SHA, pushes them to GHCR and deploys them over SSH to a GCP VM. Prometheus, Grafana and node_exporter monitor the host.
3. **Kubernetes on Minikube.** Migrations run as Jobs, and the stack adds rolling updates with zero unavailability, startup, readiness and liveness probes, CPU-based autoscaling, StatefulSet-backed RabbitMQ and an NGINX Ingress.

### At a glance

| | |
|---|---|
| **API surface** | 43 REST endpoints across 13 routers, with OpenAPI docs generated automatically |
| **Data model** | 21 relational tables, 7 triggers, 3 analytical views, 1 SQL function, 4 Alembic revisions |
| **Persistence** | PostgreSQL for transactional data, MongoDB for high-volume activity logs |
| **Async work** | Outbox-style email queue → RabbitMQ (durable queue, persistent messages) → worker |
| **Runtime** | Docker Compose (local and GCP VM) and Kubernetes (Minikube) |
| **Load data** | `bulk_seed.py` generates 200,000 products with inventory, to test queries and indexes at scale |

---

## Features

**Buyers:** browse and filter the catalog, cart, saved addresses, coupon-aware checkout, simulated payments, order history, wishlist, reviews, in-app notifications and support tickets.

**Sellers:** list products (each one waits for admin moderation), manage stock and reorder thresholds, see sales analytics and get automatic **low-stock alerts** from a database trigger.

**Admins:** manage users and roles, moderate products, view platform-wide orders, see analytics (top sellers, monthly revenue, active customers) and read the **SQL audit log** of product deletions.

**Platform:** JWT authentication, role-based access control enforced through FastAPI dependencies, activity logging to MongoDB, and top-seller recommendations served from a SQL view.

---

## Architecture

<p align="center">
  <img src="./docs/images/k8s-architecture-diagram.png" width="85%" alt="MarketGrid Kubernetes architecture"/>
</p>

```mermaid
flowchart LR
    U([User]) --> ING[NGINX Ingress<br/>ecommerce.local]
    ING -- "/" --> FE[Frontend<br/>React SPA on NGINX<br/>2 replicas]
    ING -- "/api" --> BE[Backend<br/>FastAPI<br/>HPA 2 to 5 replicas]

    BE -- "ACID transactions" --> PG[(PostgreSQL 16<br/>PVC 5Gi)]
    BE -- "activity logs" --> MG[(MongoDB 7<br/>PVC 5Gi)]
    BE -- "publish email job" --> MQ[[RabbitMQ<br/>StatefulSet]]
    MQ -- "consume" --> W[Email worker]
    W -- "mark sent / failed" --> PG

    MS[Metrics Server] -.-> HPA{{HPA<br/>CPU 60%}} -.-> BE
    JOB[Jobs:<br/>alembic upgrade<br/>seed] -.-> PG
```

| Component | Responsibility |
|---|---|
| **NGINX Ingress** | Single entry point; routes `/api` to the backend and everything else to the SPA |
| **Backend (FastAPI)** | Auth, RBAC, catalog, checkout and analytics; stateless, so it scales horizontally |
| **PostgreSQL** | Source of truth for users, inventory, orders and payments; enforces invariants with constraints and triggers |
| **MongoDB** | Append-heavy logs (product views, recommendations, user activity, notifications, support chats) |
| **RabbitMQ** | Durable queue that decouples payment confirmation from email delivery |
| **Email worker** | Consumes jobs one at a time, updates delivery state and records failures |

---

## Engineering decisions

These are the decisions that shaped the system, and why I made them.

### 1. Checkout is a single ACID transaction with deadlock-safe row locks

`OrderCheckoutService` ([`order_transaction.py`](backend/app/services/order_transaction.py)) runs the whole checkout in one transaction:

```text
validate cart and address → validate coupon
→ lock inventory rows (SELECT ... FOR UPDATE), ordered by product_id
→ check stock and moderation status → compute totals
→ insert order, order_items and payment → clear cart → COMMIT
(any exception → ROLLBACK, so no partial order can exist)
```

- **Pessimistic locking** with `SELECT ... FOR UPDATE` on `inventory` stops two concurrent checkouts from both reading `qty = 1` and overselling.
- **Locks are always taken in `product_id` order.** If two carts share products, sorting gives every transaction the same lock order, which rules out lock-ordering deadlocks.
- **Stock is decremented by a trigger** (`trg_after_order_item_insert`) in the same transaction, so stock and order items never disagree.
- A `simulate_failure` flag forces a failure after the locks are taken, to show that the rollback leaves no trace.

### 2. Notifications use a transactional outbox, not a fire-and-forget publish

Publishing to RabbitMQ inside a request has a classic failure mode: the DB commit succeeds but the publish fails, or the reverse. MarketGrid avoids that this way:

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant PG as PostgreSQL
    participant MQ as RabbitMQ
    participant W as Email worker
    API->>PG: UPDATE payments SET status='Success'
    Note over PG: trigger fn_enqueue_payment_success_email<br/>INSERT INTO email_queue (status='pending')<br/>ON CONFLICT (payment_id) DO NOTHING
    PG-->>API: COMMIT (payment + email job are atomic)
    API->>MQ: publish {email_queue_id} (durable, delivery_mode=2)
    API->>PG: status: pending → published
    MQ->>W: deliver (prefetch=1)
    W->>PG: status → sent  (or failed + last_error)
    W-->>MQ: ack (or nack, no requeue)
```

- **The email job is written by a trigger in the same transaction as the payment.** A successful payment always has exactly one email job, because `UNIQUE(payment_id)` plus `ON CONFLICT DO NOTHING` makes the insert idempotent.
- **Every state change is persisted** (`pending → published → sent | failed`, with `last_error`), so jobs that fail or are never published can be inspected and replayed from SQL.
- **Worker safety:** durable queue, persistent messages, manual acks, `prefetch_count=1` and a reconnect loop with backoff. Poison messages are nacked without requeue, so one bad job can't block the queue.

> Delivery itself is simulated (the worker logs the email); swapping in SMTP or SES only changes `process_message`.

### 3. Business invariants live in the database

Rules that must hold no matter which code path writes the data are enforced by PostgreSQL:

| Mechanism | What it does |
|---|---|
| `CHECK` / `UNIQUE` / `FK` constraints | Non-negative stock and prices, unique emails, `ON DELETE CASCADE` / `RESTRICT` chosen per relationship |
| `trg_after_order_item_insert` | Decrements inventory atomically with the order |
| `trg_inventory_low_stock` | Notifies the seller when stock drops below their reorder threshold |
| `trg_payment_*_completed` | Moves the order from `pending` to `confirmed` when its payment succeeds |
| `trg_before_product_delete_audit` | Writes the deleted row to `sql_audit_log` as JSON |
| `v_top_selling_products`, `v_monthly_sales`, `v_active_customers` | Pre-defined analytics used by the admin dashboard and the recommendations endpoint |
| Composite indexes, e.g. `(status, created_at DESC)` | Match the actual query patterns for order listings and the email queue |

Schema changes go only through **Alembic migrations**. They run as a Kubernetes `Job` before the app rolls out, never on app startup in the cluster. The schema is normalized to 3NF and RBAC is modeled relationally (`users ↔ user_roles ↔ roles ↔ role_permissions ↔ permissions`).

<p align="center">
  <img src="./docs/images/er-diagram.png" width="100%" alt="ER diagram"/>
</p>

See [`docs/DATABASE.md`](docs/DATABASE.md) for the full schema, the normalization walkthrough and indexing notes.

### 4. Polyglot persistence, for a reason

Product views and activity events are high-volume, schema-flexible and append-only. Writing them into PostgreSQL would bloat the transactional tables and compete for the same connections. They go to MongoDB, while anything that needs consistency stays relational.

### 5. Kubernetes manifests designed for zero-downtime operation

| Concern | Implementation |
|---|---|
| **Zero-downtime rollouts** | `RollingUpdate` with `maxSurge: 1`, `maxUnavailable: 0` |
| **Health semantics** | `startupProbe` (allows up to 150s for cold starts) → `readinessProbe` on `/ready` (gates traffic) → `livenessProbe` on `/health` (restarts hung pods) |
| **Graceful shutdown** | `terminationGracePeriodSeconds: 30` so in-flight requests can finish |
| **Autoscaling** | HPA scales from 2 to 5 replicas at 60% CPU; it scales up quickly (+100% per 60s) and down slowly (−50% per 60s with a 60s stabilization window) to avoid flapping |
| **Resource governance** | Requests and limits on every backend pod (`100m to 500m` CPU, `256 to 512Mi` memory) so HPA percentages and scheduling are meaningful |
| **Stateful services** | RabbitMQ as a `StatefulSet` with `volumeClaimTemplates`; PostgreSQL and MongoDB on `PersistentVolumeClaim`s |
| **Config and secrets** | Non-sensitive config in `ConfigMap`s; credentials in `Secret`s created with `kubectl` and **kept out of git** (`secret.yaml` is gitignored) |
| **Migrations and seeding** | One-off `Job`s (`backoffLimit: 3`) instead of init logic in the app container |
| **Isolation** | Separate `ecommerce` and `monitoring` namespaces |

### 6. Immutable, traceable releases

The CD pipeline tags every image with the **commit SHA** (and also `latest`), pushes it to GHCR and deploys that exact tag. Any running container can be traced back to a commit, and rolling back means redeploying an earlier SHA instead of rebuilding.

---

## CI/CD

```mermaid
flowchart LR
    P[push / PR] --> CI
    subgraph CI [ci.yml]
      F[Frontend: npm ci + build]
      B[Backend: install + compileall]
      F & B --> D[Validate both compose files<br/>Build both images with Buildx]
    end
    M[push to main] --> CD
    subgraph CD [cd.yml]
      BP[Build + push to GHCR<br/>tag = commit SHA] --> DEP[SCP compose to GCP VM<br/>SSH: pull + up -d + prune]
    end
```

- **CI** runs on every push and pull request. It builds the frontend, byte-compiles the backend, validates the dev and prod Compose files and builds both Docker images.
- **CD** runs on `main`. It pushes SHA-tagged images to GHCR, copies the production Compose file to the VM over SCP and runs `docker compose pull && up -d` over SSH. The deploy fails fast if `.env.prod` is missing on the host.
- The step-by-step VM setup is in [`docs/GCP_VM_DEPLOY.md`](docs/GCP_VM_DEPLOY.md).

---

## Observability

- **Host metrics:** node_exporter → Prometheus (5s scrape interval) → Grafana, with Prometheus provisioned as a Grafana datasource (`prometheus.yml`, `grafana.yml`).
- **Autoscaling metrics:** in the cluster, the Kubernetes **Metrics Server** feeds the HPA. Short-lived scaling signals are kept separate from long-term Prometheus storage.
- **Application logs:** structured activity documents in MongoDB, and email-job state with error messages in PostgreSQL.

---

## Quick start

### Prerequisites

Docker with the Compose plugin. Minikube and kubectl are needed only for the Kubernetes path.

### Run with Docker Compose

```bash
git clone https://github.com/Anantha-Shayan/ecommerce.git
cd ecommerce
```

Create a `.env` file in the repo root:

```env
POSTGRES_USER=marketgrid
POSTGRES_PASSWORD=change-me
POSTGRES_DB=ecommerce
DATABASE_URL=postgresql+psycopg2://marketgrid:change-me@postgres:5432/ecommerce
RABBITMQ_USER=marketgrid
RABBITMQ_PASSWORD=change-me
RABBITMQ_URL=amqp://marketgrid:change-me@rabbitmq:5672/%2F
JWT_SECRET=replace-with-a-long-random-string
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=change-me
```

```bash
docker compose up --build
```

On startup the backend runs `alembic upgrade head`, seeds demo data and then starts Uvicorn.

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API docs (Swagger UI) | http://localhost:8001/docs |
| RabbitMQ management | http://localhost:15672 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

To load-test with a large catalog:

```bash
docker compose exec backend python scripts/bulk_seed.py   # inserts 200,000 products with inventory
```

---

## Deploying to Kubernetes (Minikube)

```bash
# 1. Cluster and add-ons
minikube start
minikube addons enable ingress
minikube addons enable metrics-server

# 2. Build images inside Minikube's Docker daemon
eval $(minikube docker-env)
docker build -t ecommerce-backend:latest ./backend
docker build -t ecommerce-frontend:latest --build-arg VITE_API_URL=/api ./frontend

# 3. Namespaces
kubectl apply -f k8s/namespace/

# 4. Secrets (never committed)
kubectl -n ecommerce create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=marketgrid --from-literal=POSTGRES_PASSWORD=<pw> --from-literal=POSTGRES_DB=ecommerce
kubectl -n ecommerce create secret generic mongo-secret \
  --from-literal=MONGODB_USER=marketgrid --from-literal=MONGODB_PASS=<pw>
kubectl -n ecommerce create secret generic backend-secret \
  --from-literal=DATABASE_URL=postgresql+psycopg2://marketgrid:<pw>@postgres-service:5432/ecommerce \
  --from-literal=MONGO_URI=mongodb://marketgrid:<pw>@mongo-service:27017 \
  --from-literal=RABBITMQ_USER=marketgrid --from-literal=RABBITMQ_PASSWORD=<pw> \
  --from-literal=RABBITMQ_URL=amqp://marketgrid:<pw>@rabbitmq:5672/%2F \
  --from-literal=JWT_SECRET=<long-random-string>

# 5. Stateful services, then migrate and seed, then the app
kubectl apply -f k8s/postgres/ -f k8s/mongo/ -f k8s/rabbitmq/
kubectl apply -f k8s/backend/configmap.yaml
kubectl apply -f k8s/backend/migration-job.yaml && kubectl -n ecommerce wait --for=condition=complete job/backend-migration
kubectl apply -f k8s/backend/seed-job.yaml
kubectl apply -f k8s/backend/ -f k8s/frontend/ -f k8s/ingress/

# 6. Verify
kubectl -n ecommerce get pods,svc,ingress,hpa
echo "$(minikube ip) ecommerce.local" | sudo tee -a /etc/hosts
```

Open **http://ecommerce.local**. To watch autoscaling, generate load against `/api/products/` and run `kubectl -n ecommerce get hpa -w`.

> Service hostnames in the secrets must match the `Service` names in `k8s/*/service.yaml`.

---

## API

Interactive docs are available at `/docs` (Swagger UI) and `/redoc`. Some representative endpoints:

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/auth/register`, `/api/auth/login` | Public | Create an account / get a JWT |
| `GET` | `/api/products/` | Public | Catalog listing with filters |
| `POST` | `/api/cart/` | Buyer | Add an item to the cart |
| `POST` | `/api/orders/checkout` | Buyer | **Transactional checkout** (supports coupons and `simulate_failure`) |
| `POST` | `/api/orders/{id}/simulate-payment` | Buyer | Confirm a payment → order confirmation and email job via triggers |
| `POST` | `/api/products/seller` | Seller | List a product (enters the moderation queue) |
| `GET` | `/api/seller/analytics/sales` | Seller | Sales analytics for the seller's products |
| `PATCH` | `/api/admin/products/{id}/moderation` | Admin | Approve or reject a product |
| `GET` | `/api/admin/analytics/monthly` | Admin | Monthly revenue from `v_monthly_sales` |
| `GET` | `/api/admin/audit/sql` | Admin | Audit trail written by triggers |
| `GET` | `/health`, `/ready` | Infra | Liveness and readiness probes |

---

## Project structure

```text
ecommerce/
├── .github/workflows/      # ci.yml (build + validate), cd.yml (GHCR + GCP VM deploy)
├── backend/
│   ├── alembic/versions/   # schema, triggers, views and the email outbox migration
│   ├── app/
│   │   ├── api/            # auth and RBAC dependencies
│   │   ├── routes/         # 13 routers (auth, products, orders, admin, seller, ...)
│   │   ├── services/       # checkout transaction, email publisher, Mongo logging
│   │   ├── workers/        # RabbitMQ email consumer
│   │   ├── models/         # SQLAlchemy ORM (21 tables)
│   │   └── schemas/        # Pydantic DTOs
│   └── scripts/            # seed.py, bulk_seed.py (200k rows)
├── frontend/               # React 18 + Vite + Tailwind, served by NGINX (multi-stage build)
├── k8s/
│   ├── namespace/          # ecommerce, monitoring
│   ├── backend/            # Deployment, Service, HPA, ConfigMap, migration and seed Jobs
│   ├── frontend/  ingress/
│   ├── postgres/  mongo/   # Deployments + PVCs + Services
│   ├── rabbitmq/           # StatefulSet + Service
│   └── monitoring/         # Prometheus (in progress)
├── deploy/                 # production compose + env template for the GCP VM
├── docs/                   # DATABASE.md, GCP_VM_DEPLOY.md, DEMO_REPORT.md, diagrams
├── docker-compose.yml      # full local stack, including the worker and monitoring
├── prometheus.yml  grafana.yml
```

---

## Roadmap

| Status | Item |
|---|---|
| ✅ | ACID checkout, triggers, views, audit log, RBAC |
| ✅ | Outbox-style email pipeline over RabbitMQ with a dedicated worker |
| ✅ | Docker Compose with CI/CD to a GCP VM through GHCR |
| ✅ | Kubernetes: Ingress, rolling updates, probes, HPA, StatefulSet, migration Jobs |
| 🚧 | Prometheus and Grafana inside the cluster (`monitoring` namespace) |
| 🚧 | Email worker as a Kubernetes Deployment (runs in Compose today) |
| 🔜 | A relay that republishes `pending` email jobs if the in-request publish fails |
| 🔜 | k6 load tests to characterize HPA behavior; pytest suite in CI |
| 🔜 | Helm chart, NetworkPolicies, postgres_exporter and rabbitmq_exporter |
| 🔜 | Managed cloud deployment (EKS or GKE with managed PostgreSQL) |

---

<div align="center">

Built by **[Anantha Shayan](https://github.com/Anantha-Shayan)** · [Portfolio](https://ananthadev.online) · [LinkedIn](https://www.linkedin.com/in/anantha-shayan28022006/)

</div>
