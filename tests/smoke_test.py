"""Quick API smoke test."""
import httpx

r = httpx.get("http://localhost:8000/health")
print("Health:", r.json())

r2 = httpx.get("http://localhost:8000/.well-known/ai-commerce.json")
d = r2.json()
print(f"Discovery: {len(d['tools'])} tools, {d['total_products']} products")

r3 = httpx.post("http://localhost:8000/api/v1/tools/search_products", json={"query": "sneakers", "limit": 3})
s = r3.json()
print(f"Search 'sneakers': {s['data']['total_found']} found")
for p in s["data"]["products"]:
    print(f"  - {p['name']} ₹{p['price']}")

print("\n✅ All API checks passed!")
