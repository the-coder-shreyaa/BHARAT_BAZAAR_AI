"""
Full E2E verification against live FastAPI server.
"""
import httpx, time, sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"

API = "http://localhost:8000"

for i in range(5):
    try:
        httpx.get(f"{API}/health", timeout=2)
        break
    except Exception:
        time.sleep(2)

print("=" * 60)
print("  BHARAT BAZAAR AI - Full E2E Verification")
print("=" * 60)

print("\n[1/9] Health Check...")
r = httpx.get(f"{API}/health")
assert r.status_code == 200
print(f"  OK - Status: {r.json()['status']}")

print("\n[2/9] Discovery Manifest...")
r = httpx.get(f"{API}/.well-known/ai-commerce.json")
d = r.json()
print(f"  OK - Merchant: {d['merchant_name']}, Tools: {len(d['tools'])}, Products: {d['total_products']}")

print("\n[3/9] Search: sneakers under 2000...")
r = httpx.post(f"{API}/api/v1/tools/search_products", json={"query": "sneakers", "max_price": 2000, "limit": 5})
assert r.json()["success"]
products = r.json()["data"]["products"]
print(f"  OK - Found {r.json()['data']['total_found']} products")
for p in products[:3]:
    print(f"     - {p['name']} - Rs.{p['price']}")
product_id = products[0]["product_id"]
product_name = products[0]["name"]

print(f"\n[4/9] Product Details: {product_name}...")
r = httpx.get(f"{API}/api/v1/tools/products/{product_id}")
assert r.json()["success"]
p = r.json()["data"]
print(f"  OK - Price: Rs.{p['price']}, Category: {p['category']}")

print(f"\n[5/9] Stock Check...")
r = httpx.get(f"{API}/api/v1/tools/products/{product_id}/stock")
assert r.json()["success"]
s = r.json()["data"]
print(f"  OK - Available: {s['available']}, Stock: {s['stock']} units")

print("\n[6/9] Create Cart...")
r = httpx.post(f"{API}/api/v1/tools/cart", json={"session_id": "e2e-verify"})
assert r.json()["success"]
cart_id = r.json()["data"]["cart_id"]
print(f"  OK - Cart: {cart_id}")

print(f"\n[7/9] Add to Cart: {product_name} x1...")
r = httpx.post(f"{API}/api/v1/tools/cart/{cart_id}/items", json={"product_id": product_id, "quantity": 1})
assert r.json()["success"]
print(f"  OK - Items: {r.json()['data']['item_count']}, Total: Rs.{r.json()['data']['total']}")

print("\n[8/9] Create Order...")
r = httpx.post(f"{API}/api/v1/tools/orders", json={"cart_id": cart_id, "session_id": "e2e-verify"})
assert r.json()["success"]
order = r.json()["data"]
order_id = order["order_id"]
print(f"  OK - Order: {order_id}, Total: Rs.{order['total_amount']}, Status: {order['status']}")

print(f"\n[9/9] Checkout...")
r = httpx.post(f"{API}/api/v1/tools/orders/{order_id}/checkout")
assert r.json()["success"]
co = r.json()["data"]
print(f"  OK - Mode: {co['payment_mode']}, Amount: Rs.{co['amount']}, Status: {co['status']}")

print("\n[BONUS] Audit Logs...")
r = httpx.get(f"{API}/api/v1/tools/audit/logs", params={"session_id": "e2e-verify"})
assert r.json()["success"]
print(f"  OK - {len(r.json()['data'])} audit entries logged")

print("\n[BONUS] Growth Insights...")
r = httpx.get(f"{API}/api/v1/tools/growth/insights")
assert r.json()["success"]
print(f"  OK - {len(r.json()['data'])} recommendations")

print("\n" + "=" * 60)
print("  ALL E2E CHECKS PASSED - SYSTEM FULLY OPERATIONAL")
print("=" * 60)
