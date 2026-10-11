# OrderFlow

Multi-vendor order & inventory REST API (Flask, PostgreSQL, JWT/RBAC) with row-level locking to prevent overselling.

## Problem it solves

In a multi-vendor store two customers can try to buy the last product at the same moment. If the app only checks the stock and then updates it, both requests can pass the check before either one saves, so both orders succeed and stock goes negative. OrderFlow prevents this by locking the row with `SELECT... FOR UPDATE` while the order is processed. The second request waits until the first is completed, then reads the updated stock of 0 and is rejected with an insufficient-stock error.

## Tech stack

- Flask
- PostgreSQL with SQLAlchemy (Flask-SQLAlchemy)
- Alembic migrations (Flask-Migrate)
- JWT authentication (Flask-JWT-Extended)

## Features

- Register and login with hashed passwords and JWT access tokens
- Role-based access control for customers, sellers and admins
- Public product listing; product creation restricted to sellers and admins
- Order placement that locks product rows (`SELECT ... FOR UPDATE`) and rolls back if any item lacks stock
- Order status state machine (pending, confirmed, shipped, delivered, cancelled) with validated transitions
- Concurrency test: 5 simultaneous requests for a 1-unit product produce exactly 1 successful order

## API endpoints

| Method | Path | Who can call it | Success status |
|--------|------|-----------------|----------------|
| POST | `/api/auth/register` | Anyone | 201 |
| POST | `/api/auth/login` | Anyone | 200 |
| GET  | `/api/products/` | Anyone | 200 |
| POST | `/api/products/` | Seller/admin | 201 |
| POST | `/api/orders/` | Logged in | 201 |
| PATCH | `/api/orders/<order_id>/status` | Logged in | 200 |