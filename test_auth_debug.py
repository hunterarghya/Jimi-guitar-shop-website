#!/usr/bin/env python3
"""Debug authentication issue"""
import requests
import json

BASE_URL = "http://localhost:8000"

# First login to get token
print("1. Logging in as admin...")
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "email": "pahaariaexpress@gmail.com",
        "password": "admin123"
    }
)

if login_response.status_code == 200:
    tokens = login_response.json()
    access_token = tokens["access_token"]
    print(f"✓ Login successful")
    print(f"Token (first 50 chars): {access_token[:50]}...")
    
    # Now try to access admin dashboard with token
    print("\n2. Accessing admin dashboard...")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    dashboard_response = requests.get(
        f"{BASE_URL}/api/v1/admin/dashboard",
        headers=headers
    )
    
    print(f"Status: {dashboard_response.status_code}")
    print(f"Response: {dashboard_response.text[:200]}")
    
    if dashboard_response.status_code == 200:
        print("✓ Admin dashboard accessible!")
    else:
        print("✗ Admin dashboard returned 401")
else:
    print(f"✗ Login failed: {login_response.status_code}")
    print(login_response.text)
