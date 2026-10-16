import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models.user import User, UserRole

PASSWORD = "pass12345"


@pytest.fixture
def app():
  app = create_app(TestConfig)
  assert "orderflow_test" in app.config["SQLALCHEMY_DATABASE_URI"]
  with app.app_context():
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()


@pytest.fixture
def client(app):
  return app.test_client()


def make_headers(client, email, role):
  user = User(email=email, role=role)
  user.set_password(PASSWORD)
  db.session.add(user)
  db.session.commit()
  response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
  return {"Authorization": "Bearer " + response.get_json()["access_token"]}


@pytest.fixture
def customer_headers(client):
  return make_headers(client, "customer@example.com", UserRole.CUSTOMER)


@pytest.fixture
def other_customer_headers(client):
  return make_headers(client, "other@example.com", UserRole.CUSTOMER)


@pytest.fixture
def seller_headers(client):
  return make_headers(client, "seller@example.com", UserRole.SELLER)


@pytest.fixture
def admin_headers(client):
  return make_headers(client, "admin@example.com", UserRole.ADMIN)


@pytest.fixture
def product(client, seller_headers):
  response = client.post(
    "/api/products/",
    json={"name": "Wireless Mouse", "price_cents": 1999, "stock_quantity": 10},
    headers=seller_headers,
  )
  return response.get_json()