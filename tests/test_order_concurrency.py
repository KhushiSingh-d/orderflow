import threading

from app.models.order import Order

NUM_REQUESTS = 5


def test_concurrent_orders_for_last_unit_only_one_succeeds(app, client, customer_headers, seller_headers):
  created = client.post(
    "/api/products/",
    json={"name": "Limited Edition Keyboard", "price_cents": 5999, "stock_quantity": 1},
    headers=seller_headers,
  )
  product_id = created.get_json()["id"]

  barrier = threading.Barrier(NUM_REQUESTS)
  results = []

  def place_order():
    worker_client = app.test_client()
    barrier.wait(timeout=10)
    response = worker_client.post(
      "/api/orders/",
      json={"items": [{"product_id": product_id, "quantity": 1}]},
      headers=customer_headers,
    )
    results.append(response.status_code)

  threads = [threading.Thread(target=place_order) for _ in range(NUM_REQUESTS)]
  for t in threads:
    t.start()
  for t in threads:
    t.join()

  assert len(results) == NUM_REQUESTS
  assert results.count(201) == 1
  assert results.count(400) == NUM_REQUESTS - 1
  assert Order.query.count() == 1

  products = client.get("/api/products/").get_json()
  stock = next(p["stock_quantity"] for p in products if p["id"] == product_id)
  assert stock == 0