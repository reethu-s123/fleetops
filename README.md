[ Client Browser / Mobile Driver ]
                                   │
                          (HTTPS:443 / WSS)
                                   │
                       ┌───────────────────────┐
                       │   Nginx Reverse Proxy │
                       │     (SSL & Statics)   │
                       └───────────┬───────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                ▼                                     ▼
    ┌───────────────────────┐             ┌───────────────────────┐
    │   Daphne ASGI Server  │             │   Django Channels     │
    │      (REST APIs)      │             │     (WebSockets)      │
    └───────────┬───────────┘             └───────────┬───────────┘
                │                                     │
                ▼                                     ▼
    ┌───────────────────────┐             ┌───────────────────────┐
    │     PostgreSQL 16     │             │        Redis 7        │
    │  (Schema Isolation    │             │   (Channel Layer &    │
    │   via django-tenants) │             │    Cache Storage)     │
    └───────────────────────┘             └───────────┬───────────┘
                                                      │
                                 ┌────────────────────┴────────────────────┐
                                 ▼                                         ▼
                     ┌───────────────────────┐                 ┌───────────────────────┐
                     │     Celery Worker     │                 │      Celery Beat      │
                     │   • AI ML Inference   │                 │   • Daily Expiry Scan │
                     │   • PDF Invoices      │                 │   • Scheduled Crons   │
                     └───────────────────────┘                 └───────────────────────┘


---

## 🌟 Core Feature Modules

| Module | Engineering Pattern | Tech Stack |
| :--- | :--- | :--- |
| **Multi-Tenancy** | Schema-per-tenant data isolation, zero data bleed between companies | `django-tenants`, PostgreSQL Schemas |
| **RBAC Security** | Granular user roles: System Admin, Tenant Owner, Dispatcher, Driver | JWT Auth, Custom User Model |
| **Shipment Lifecycle** | Deterministic Finite State Machine guarding against illegal transitions | `django-fsm-2` |
| **Route Optimization** | OSRM Highway Turn-by-Turn polyline routing & address geocoding | OpenStreetMap, Nominatim, OSRM |
| **Real-Time Telemetry** | Low-latency GPS coordinate ingestion with heading angle compass rotation | Django Channels, WebSockets, Redis |
| **AI Delay Predictor** | Random Forest Classifier trained on route distance, weight, and weather | `scikit-learn`, Open-Meteo Satellite API |
| **Automated Invoicing** | Dynamic, itemized PDF invoice generation upon delivery confirmation | `ReportLab`, Celery Workers |
| **Executive Dashboard** | Sub-15ms cached analytics using database-level SQL aggregations | PostgreSQL `Sum`/`Count`/`Avg`, Redis Cache |

---

## 💰 Zero-Cost Stack Integration

This entire enterprise platform operates with **zero API subscription costs**:
* **OSRM (Open Source Routing Machine):** Free turn-by-turn routing and highway distance.
* **Open-Meteo API:** Real-time satellite weather and temperature without API keys.
* **Leaflet + OpenStreetMap Humanitarian:** High-contrast street mapping.
* **PostgreSQL & Redis:** Open-source local containerized cluster.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* Git installed.

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/fleetops.git
cd fleetops
