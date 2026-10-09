import threading
import requests

LOGIN_URL = "http://127.0.0.1:5000/api/auth/login"
ORDER_URL = "http://127.0.0.1:5000/api/orders/"
PRODUCT_ID = 2
NUM_REQUESTS = 5

response = requests.post(LOGIN_URL, json={"email": "test@example.com", "password": "mypassword123"})
token = response.json()["access_token"]

results = []

def place_order():
  headers = {"Authorization": f"Bearer {token}"}
  response = requests.post(ORDER_URL, json={"items": [{"product_id": PRODUCT_ID, "quantity": 1}]}, headers=headers)
  results.append(response.status_code)

threads = [threading.Thread(target=place_order) for _ in range(NUM_REQUESTS)]

for t in threads:
  t.start()

for t in threads:
  t.join()

print("Results:", results)
print("Successes (201):", results.count(201))
print("Failures (400):", results.count(400))