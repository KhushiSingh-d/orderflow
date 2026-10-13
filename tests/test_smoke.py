def test_ping(client):
  response = client.get("/api/auth/ping")
  assert response.status_code == 200


def test_register_creates_customer(client):
  response = client.post("/api/auth/register", json={"email": "a@example.com", "password": "pass12345"})
  assert response.status_code == 201
  assert response.get_json()["role"] == "customer"


def test_register_rejects_admin_role(client):
  response = client.post("/api/auth/register", json={"email": "b@example.com", "password": "pass12345", "role": "admin"})
  assert response.status_code == 400