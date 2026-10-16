def stock_of(client, product_id):
  products = client.get("/api/products/").get_json()
  return next(p["stock_quantity"] for p in products if p["id"] == product_id)


def place_order(client, headers, product_id, quantity):
  return client.post(
    "/api/orders/",
    json={"items": [{"product_id": product_id, "quantity": quantity}]},
    headers=headers,
  )


def set_status(client, headers, order_id, status):
  return client.patch(
    f"/api/orders/{order_id}/status",
    json={"status": status},
    headers=headers,
  )


def test_customer_places_order_and_stock_drops(client, customer_headers, product):
  response = place_order(client, customer_headers, product["id"], 2)
  assert response.status_code == 201
  assert response.get_json()["total_cents"] == 2 * 1999
  assert stock_of(client, product["id"]) == 8


def test_order_rejected_when_stock_is_insufficient(client, customer_headers, product):
  response = place_order(client, customer_headers, product["id"], 11)
  assert response.status_code == 400
  assert stock_of(client, product["id"]) == 10


def test_seller_cannot_place_order(client, seller_headers, product):
  response = place_order(client, seller_headers, product["id"], 1)
  assert response.status_code == 403


def test_negative_quantity_is_rejected(client, customer_headers, product):
  response = place_order(client, customer_headers, product["id"], -5)
  assert response.status_code == 400
  assert stock_of(client, product["id"]) == 10


def test_customer_cannot_cancel_someone_elses_order(client, customer_headers, other_customer_headers, product):
  order = place_order(client, customer_headers, product["id"], 1).get_json()
  response = set_status(client, other_customer_headers, order["id"], "cancelled")
  assert response.status_code == 403


def test_customer_cannot_ship_own_order(client, customer_headers, product):
  order = place_order(client, customer_headers, product["id"], 1).get_json()
  response = set_status(client, customer_headers, order["id"], "shipped")
  assert response.status_code == 403


def test_cancel_restores_stock_only_once(client, customer_headers, product):
  order = place_order(client, customer_headers, product["id"], 3).get_json()
  assert stock_of(client, product["id"]) == 7

  first = set_status(client, customer_headers, order["id"], "cancelled")
  assert first.status_code == 200
  assert stock_of(client, product["id"]) == 10

  second = set_status(client, customer_headers, order["id"], "cancelled")
  assert second.status_code == 400
  assert stock_of(client, product["id"]) == 10


def test_admin_can_confirm_order(client, customer_headers, admin_headers, product):
  order = place_order(client, customer_headers, product["id"], 1).get_json()
  response = set_status(client, admin_headers, order["id"], "confirmed")
  assert response.status_code == 200
  assert response.get_json()["status"] == "confirmed"