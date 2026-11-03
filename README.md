# 🚚 FleetOps — Multi-Tenant AI-Powered Logistics & Fleet Management SaaS

[![Django](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

**FleetOps** is an enterprise-grade B2B SaaS platform where logistics companies manage vehicles, drivers, multi-stop shipments, real-time GPS tracking, automated PDF billing, and AI-driven delay predictions.

Built with **PostgreSQL Schema-per-Tenant isolation**, **Django Channels WebSockets**, **Celery Distributed Workers**, and **scikit-learn Machine Learning**.

---

## 🏛️ System Architecture

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
