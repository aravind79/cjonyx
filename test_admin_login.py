#!/usr/bin/env python
"""Test the complete admin login flow"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create session with retry strategy
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)

BASE_URL = 'http://127.0.0.1:5000'

print("\n=== TESTING ADMIN LOGIN FLOW ===\n")

# Step 1: Get login page
print("[1] Getting login page...")
r = session.get(f'{BASE_URL}/login')
print(f"    Status: {r.status_code}")

# Step 2: Login
print("\n[2] Submitting login form...")
data = {'username': 'admin', 'password': 'admin123'}
r = session.post(f'{BASE_URL}/login', data=data, allow_redirects=False)
print(f"    Status: {r.status_code}")
print(f"    Location: {r.headers.get('Location', 'None')}")
print(f"    Cookies: {session.cookies}")

# Step 3: Check session via debug endpoint
print("\n[3] Checking session...")
r = session.get(f'{BASE_URL}/debug/session')
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    import json
    data = r.json()
    print(f"    user_id: {data.get('user_id')}")
    print(f"    username: {data.get('username')}")
    print(f"    is_admin: {data.get('is_admin')}")
else:
    print(f"    Response: {r.text}")

# Step 4: Try to access admin dashboard
print("\n[4] Accessing /admin...")
r = session.get(f'{BASE_URL}/admin', allow_redirects=False)
print(f"    Status: {r.status_code}")
print(f"    Location: {r.headers.get('Location', 'None')}")

print("\n")
