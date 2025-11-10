# GeoLocal E-Commerce Delivery Marketplace

## Overview
A modern Django REST backend for a local delivery marketplace enabling users to discover nearby merchants, browse products, place atomic orders, and track deliveries with geo search and real-time analytics. Built for performance, scalability, and production-grade concurrency.

## Domain Data Model

**Key Models**
- **User**: Platform user (Django built-in).
- **Merchant**: OneToOne mapped to User; holds merchant info, categories, address, geospatial delivery zones.
- **Address**: Full address with Point geometry field (PostGIS), used for merchants and orders.
- **ProductCategory**: Defines product groupings.
- **Product**: Belongs to category & merchant. Price, description, published status.
- **Inventory**: Stock count for each (Merchant, Product). Updated with row-level locks for race-safe operations.
- **Order**: References buyer (User), merchant, address. Includes status/state, total, timestamps.
- **OrderItem**: Line items with quantity, product, price breakdown.
- **DeliveryZone**: Polygon-based area assigned to merchants.

**Key Constraints**
- Unique and GiST-indexed geo fields for spatial queries
- Foreign keys with select_related/prefetch for optimal ORM use

## Main Features
- **Merchant & Product CRUD**: Full API endpoints for management, using DRF ViewSets and serializers.
- **Spatial Search**: /api/custom/products/nearby/ returns products in radius of a (lat,lng).
- **Atomic Orders**: Robust transaction handling with savepoints, race-safe stock decrement (select_for_update).
- **Inventory Management**: Prevents overselling under heavy concurrency using row-level DB locks.
- **Redis Caching**: Frequently accessed product/merchant search results cached with TTL and versioned keys, auto-invalidation.
- **Async Delivery ETA**: Async endpoint for delivery ETA calculation (using asyncio; pluggable for real mapping APIs).
- **Analytics (CTE/Window Functions)**: Top-selling products per merchant, complex reporting via annotated subqueries at /api/custom/orders/analytics/.
- **Priority Assignment**: Assigns orders to couriers based on geo proximity (route: /api/custom/orders/priority-assignment/).

## Architecture
- **Tech Stack**: Python 3.11, Django 4+, DRF, PostgreSQL + PostGIS, Redis, dockerized for scalability
- **Patterns**: Layered (models/services/views), Repository/Service for business logic, DTOs for API
- **API**: Versioned (v1) resource-based endpoints; DRF viewsets for resources, APIViews for business actions
- **Authentication**: DRF token/session authentication, per-project requirements
- **Async/Concurrent Support**: asyncio for delivery estimate aggregation, row-level PG locks for inventory and orders

## API Endpoints (sample)
- `/api/merchants/` (CRUD)
- `/api/products/` (CRUD)
- `/api/custom/products/nearby/?lat=..&lng=..&radius=..` (spatial search)
- `/api/inventories/` (CRUD)
- `/api/orders/` (CRUD)
- `/api/custom/orders/analytics/` (analytics)
- `/api/custom/orders/priority-assignment/` (courier assignment)
- `/api/delivery/eta/` (POST: async ETA)

## Concurrency & Data Integrity
- Order placement and inventory adjustments fully atomic, safe under parallel client load (see test_concurrent_inventory_decrement)

## Caching
- Redis used for popular geo/product search caching; TTL, versioned invalidation on inventory changes

## Extensibility
This monolithic app can be split to microservices (orders, inventory, merchant catalog, analytics, delivery etc.) as business grows. Async job queue is pluggable with Celery, and external integrations can be layered via service objects.

## For Developers
- Run `make setup && make test` to initialize and test.
- API entrypoint: `/api/` (see routers and urls for detail)

---
Production-quality, thoroughly tested (including geo/safe concurrency/async/reporting) and built to easily extend for post-launch requirements.