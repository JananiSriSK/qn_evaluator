import requests

# Test health
print("Testing health endpoint...")
r = requests.get("http://localhost:8002/")
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")
print()

# Test create domain
print("Testing create domain endpoint...")
r = requests.post("http://localhost:8002/domains/create", json={
    "user_id": "test_user",
    "domain_name": "TEST_DOMAIN"
})
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")
