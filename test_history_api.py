"""
Test History APIs
"""
import requests
import json
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"
ADMIN_AUTH = ('admin', 'changeme123')

print("\n" + "="*60)
print("🕷️  TESTING HISTORY & DATE FILTER APIS")
print("="*60 + "\n")

# Test 1: Add browsing history
print("TEST 1: Add Browsing History")
machine_id = str(uuid.uuid4())
print(f"Machine ID: {machine_id}")

for i in range(5):
    response = requests.post(
        f"{BASE_URL}/api/history",
        json={
            "machine_id": machine_id,
            "url": f"https://example.com/page{i}",
            "title": f"Example Page {i}",
            "profile_name": "TestProfile"
        }
    )
    print(f"  Added entry {i+1}: {response.status_code}")

# Test 2: Get all history
print("\nTEST 2: Get All History (Recent 100)")
response = requests.get(f"{BASE_URL}/api/history", auth=ADMIN_AUTH)
print(f"Status: {response.status_code}")
history = response.json()
print(f"Total entries: {len(history)}")
if history:
    print(f"Latest: {history[0]['url']} at {history[0]['visited_at']}")

# Test 3: Get history for specific user
print("\nTEST 3: Get History for Specific User")
response = requests.get(
    f"{BASE_URL}/api/history?machine_id={machine_id}&limit=10",
    auth=ADMIN_AUTH
)
print(f"Status: {response.status_code}")
user_history = response.json()
print(f"User entries: {len(user_history)}")

# Test 4: Get history users
print("\nTEST 4: Get History Users")
response = requests.get(f"{BASE_URL}/api/history/users", auth=ADMIN_AUTH)
print(f"Status: {response.status_code}")
users = response.json()
print(f"Total users: {len(users)}")
for user in users[:3]:
    print(f"  - {user['machine_id'][:12]}... ({user['visit_count']} visits)")

# Test 5: Date range filter
print("\nTEST 5: Date Range Filter")
today = datetime.now().strftime('%Y-%m-%d')
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

response = requests.post(
    f"{BASE_URL}/api/licenses/filter",
    auth=ADMIN_AUTH,
    json={
        "filter_type": "created",
        "start_date": today,
        "end_date": tomorrow
    }
)
print(f"Status: {response.status_code}")
filtered = response.json()
print(f"Licenses created today: {len(filtered)}")

print("\n" + "="*60)
print("✅ All history API tests completed!")
print("="*60 + "\n")
