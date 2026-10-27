# OrderFlow

Multi-vendor order & inventory REST API (Flask, PostgreSQL, JWT/RBAC) with row-level locking to prevent overselling.

## Problem it solves

In a multi-vendor store two customers can try to buy the last product at the same moment. If the app only checks the stock and then updates it, both requests can pass the check before either one saves, so both orders succeed and stock goes negative. OrderFlow prevents this by locking the row with `SELECT ... FOR UPDATE` while the order is processed. The second request waits until the first is completed, then reads the updated stock of 0 and is rejected with an insufficient-stock error.

## Tech stack

- Flask
- PostgreSQL with SQLAlchemy (Flask-SQLAlchemy) and the psycopg2 driver
- Alembic migrations (Flask-Migrate)
- JWT authentication (Flask-JWT-Extended)
- Pytest

## Features

- Register and login with hashed passwords and JWT access tokens
- Role-based access control for customers, sellers and admins
- Public product listing; product creation restricted to sellers and admins
- Order placement that locks product rows (`SELECT ... FOR UPDATE`) and rolls back if any item lacks stock
- Order status state machine (pending, confirmed, shipped, delivered, cancelled) with validated transitions
- Order rules: only customers place orders; admins make any valid status change and customers can only cancel their own orders; quantities must be positive whole numbers; public sign-up is limited to customer and seller roles
- Cancelling an order returns its items to stock, with row locks so a repeated cancel can't restore stock twice
- Concurrency test: 5 simultaneous requests for a 1-unit product produce exactly 1 successful order

## API endpoints

| Method | Path | Who can call it | Success status |
|--------|------|-----------------|----------------|
| POST | `/api/auth/register` | Anyone | 201 |
| POST | `/api/auth/login` | Anyone | 200 |
| GET | `/api/products/` | Anyone | 200 |
| POST | `/api/products/` | Seller/admin | 201 |
| POST | `/api/orders/` | Customer | 201 |
| PATCH | `/api/orders/<order_id>/status` | Admin (any valid change); customer (cancel own order only) | 200 |

## Design decisions

- **Row-level locking:** order placement locks each product row until the transaction commits, so concurrent buyers are processed one at a time per product. All items in an order succeed together or the whole order is rolled back.
- **Money as integer cents:** prices are stored as integers (`price_cents`) to avoid floating-point rounding errors.
- **Price snapshot:** each order item stores the unit price at purchase time, so order history doesn't change when a seller changes a price later.
- **State machine:** an order can only move along allowed transitions, for example a shipped order can't be cancelled.
- **Authentication and authorization:** passwords are hashed, the JWT carries the user's role, and a `role_required` decorator checks it. Ownership is checked inside the route, so customers can only cancel their own orders.
- **Login errors:** wrong email and wrong password return the same message, so the API doesn't reveal which emails are registered.

## Project structure

```
orderflow/
├── app/
│   ├── models/        # User, Product, Order, OrderItem
│   ├── routes/        # auth, products and orders blueprints
│   ├── utils/         # role_required decorator
│   ├── config.py
│   ├── extensions.py
│   └── __init__.py    # application factory
├── migrations/        # Alembic migration files
├── tests/             # Pytest fixtures and tests
├── pytest.ini
├── requirements.txt
└── .env.example
```

## Setup

1. Clone and enter the project:
   ```bash
   git clone https://github.com/KhushiSingh-d/orderflow.git
   cd orderflow
   ```
2. Create and activate a virtual environment, then install dependencies:
   ```bash
   python -m venv venv
   source venv/Scripts/activate   # macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create the PostgreSQL user and databases (run in `psql` as an admin):
   ```sql
   CREATE USER orderflow_user WITH PASSWORD 'your_password';
   CREATE DATABASE orderflow_dev OWNER orderflow_user;
   CREATE DATABASE orderflow_test OWNER orderflow_user;
   ```
4. Copy `.env.example` to `.env` and fill in `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL` and `TEST_DATABASE_URL`, using the `postgresql+psycopg2://` form, for example:
   ```
   DATABASE_URL=postgresql+psycopg2://orderflow_user:your_password@localhost:5432/orderflow_dev
   ```
5. Apply migrations and start the server:
   ```bash
   flask db upgrade
   flask run
   ```

Admin accounts can't be created through the API. To make one, register a user and promote them in SQL, then log in again to get a token that carries the new role:

```sql
UPDATE users SET role = 'ADMIN' WHERE email = 'you@example.com';
```

## Running the tests

```bash
pytest
```

12 tests cover order flows, authorization rules, stock restoration and the concurrency scenario. They run against the separate `orderflow_test` database (set `TEST_DATABASE_URL` in `.env`), which is created and cleared automatically. The tests need PostgreSQL, because the locking tests rely on `SELECT ... FOR UPDATE`, which SQLite doesn't support.

## Example walkthrough

Register and log in as a seller, then create a product:

```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "seller@example.com", "password": "pass12345", "role": "seller"}'

curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "seller@example.com", "password": "pass12345"}'

curl -X POST http://127.0.0.1:5000/api/products/ \
  -H "Authorization: Bearer <seller_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Wireless Mouse", "price_cents": 1999, "stock_quantity": 10}'
```

Register and log in as a customer (the default role), then place and cancel an order:

```bash
curl -X POST http://127.0.0.1:5000/api/orders/ \
  -H "Authorization: Bearer <customer_token>" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 2}]}'

curl -X PATCH http://127.0.0.1:5000/api/orders/1/status \
  -H "Authorization: Bearer <customer_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "cancelled"}'
```

Cancelling returns the two units to stock.

## Limitations and future improvements

- No pagination on the product list, and no endpoints to fetch a single product or list a customer's own orders
- Sellers can't yet manage the status of orders for their own products
- Product input validation is minimal (for example, price isn't checked)
- No refresh tokens or token revocation
- Docker, Redis caching and deployment are not implemented yet