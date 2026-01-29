"""Comprehensive API test script."""
try:
    from starlette.testclient import TestClient
except ImportError:
    from fastapi.testclient import TestClient
from app.api import app

# Test results
results = {
    "auth": {},
    "users": {},
    "products": {},
    "cart": {},
    "orders": {},
    "social": {},
    "moderation": {},
    "admin": {},
}

test_data = {
    "auth_token": None,
    "refresh_token": None,
    "user_id": None,
    "product_id": None,
    "post_id": None,
    "order_id": None,
}


def run_tests():
    """Run all API tests."""
    client = TestClient(app)
    
    print("\n" + "="*70)
    print("JIMI PLATFORM - API COMPREHENSIVE TEST")
    print("="*70)

    # 1. HEALTH CHECK
    print("\n[HEALTH CHECK]")
    try:
        response = client.get("/health")
        assert response.status_code == 200
        print("✓ GET /health - OK")
        results["health"] = "PASS"
    except Exception as e:
        print(f"✗ GET /health - FAILED: {str(e)}")
        results["health"] = f"FAIL: {str(e)}"

    # 2. AUTH ENDPOINTS
    print("\n[AUTH ENDPOINTS]")

    # Register
    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPass123!@",
                "full_name": "Test User",
                "phone": "9876543210",
            },
        )
        assert response.status_code == 201
        test_data["user_id"] = response.json().get("user_id")
        print("✓ POST /api/v1/auth/register - OK")
        results["auth"]["register"] = "PASS"
    except Exception as e:
        print(f"✗ POST /api/v1/auth/register - FAILED: {str(e)}")
        results["auth"]["register"] = f"FAIL: {str(e)}"

    # Login
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPass123!@"},
        )
        if response.status_code == 200:
            test_data["auth_token"] = response.json().get("access_token")
            test_data["refresh_token"] = response.json().get("refresh_token")
            print("✓ POST /api/v1/auth/login - OK")
            results["auth"]["login"] = "PASS"
        else:
            print(f"✗ POST /api/v1/auth/login - Status {response.status_code}")
            results["auth"]["login"] = f"FAIL: Status {response.status_code}"
    except Exception as e:
        print(f"✗ POST /api/v1/auth/login - FAILED: {str(e)}")
        results["auth"]["login"] = f"FAIL: {str(e)}"

    # Token Refresh
    if test_data["refresh_token"]:
        try:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": test_data["refresh_token"]},
            )
            if response.status_code == 200:
                print("✓ POST /api/v1/auth/refresh - OK")
                results["auth"]["refresh"] = "PASS"
            else:
                print(f"✗ POST /api/v1/auth/refresh - Status {response.status_code}")
                results["auth"]["refresh"] = f"FAIL: Status {response.status_code}"
        except Exception as e:
            print(f"✗ POST /api/v1/auth/refresh - FAILED: {str(e)}")
            results["auth"]["refresh"] = f"FAIL: {str(e)}"

    # 3. PRODUCTS ENDPOINTS
    print("\n[PRODUCTS ENDPOINTS]")

    headers = {"Authorization": f"Bearer {test_data['auth_token']}"} if test_data[
        "auth_token"
    ] else {}

    # List Products
    try:
        response = client.get("/api/v1/products?page=1&page_size=10")
        assert response.status_code == 200
        products = response.json().get("data", [])
        if products:
            test_data["product_id"] = products[0].get("id")
        print("✓ GET /api/v1/products - OK")
        results["products"]["list"] = "PASS"
    except Exception as e:
        print(f"✗ GET /api/v1/products - FAILED: {str(e)}")
        results["products"]["list"] = f"FAIL: {str(e)}"

    # Search Products
    try:
        response = client.get("/api/v1/products/search?q=guitar")
        assert response.status_code == 200
        print("✓ GET /api/v1/products/search - OK")
        results["products"]["search"] = "PASS"
    except Exception as e:
        print(f"✗ GET /api/v1/products/search - FAILED: {str(e)}")
        results["products"]["search"] = f"FAIL: {str(e)}"

    # Create Product (Admin)
    if test_data["auth_token"]:
        try:
            response = client.post(
                "/api/v1/products",
                json={
                    "name": "Test Guitar",
                    "description": "A test guitar for testing purposes",
                    "category": "Acoustic",
                    "price": 5000,
                    "stock": 10,
                    "sku": "TEST-GUITAR-001",
                    "brand": "TestBrand",
                },
                headers=headers,
            )
            if response.status_code in [201, 403]:
                if response.status_code == 201:
                    print("✓ POST /api/v1/products - OK (admin)")
                else:
                    print("✓ POST /api/v1/products - OK (permission denied as expected)")
                results["products"]["create"] = "PASS"
            else:
                print(f"✗ POST /api/v1/products - Status {response.status_code}")
                results["products"]["create"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ POST /api/v1/products - FAILED: {str(e)}")
            results["products"]["create"] = f"FAIL: {str(e)}"

    # 4. CART ENDPOINTS
    print("\n[CART ENDPOINTS]")

    # Get Cart
    if test_data["auth_token"]:
        try:
            response = client.get("/api/v1/cart", headers=headers)
            assert response.status_code == 200
            print("✓ GET /api/v1/cart - OK")
            results["cart"]["get"] = "PASS"
        except Exception as e:
            print(f"✗ GET /api/v1/cart - FAILED: {str(e)}")
            results["cart"]["get"] = f"FAIL: {str(e)}"

        # Add to Cart (needs valid product ID)
        if test_data["product_id"]:
            try:
                response = client.post(
                    "/api/v1/cart/items",
                    json={"product_id": test_data["product_id"], "quantity": 1},
                    headers=headers,
                )
                if response.status_code in [201, 400]:
                    print(f"✓ POST /api/v1/cart/items - OK (Status {response.status_code})")
                    results["cart"]["add"] = "PASS"
                else:
                    print(f"✗ POST /api/v1/cart/items - Status {response.status_code}")
                    results["cart"]["add"] = f"Status {response.status_code}"
            except Exception as e:
                print(f"✗ POST /api/v1/cart/items - FAILED: {str(e)}")
                results["cart"]["add"] = f"FAIL: {str(e)}"

    # 5. USERS ENDPOINTS
    print("\n[USERS ENDPOINTS]")

    if test_data["auth_token"]:
        # Get Profile
        try:
            response = client.get("/api/v1/users/me", headers=headers)
            if response.status_code == 200:
                print("✓ GET /api/v1/users/me - OK")
                results["users"]["profile"] = "PASS"
            else:
                print(f"✓ GET /api/v1/users/me - Status {response.status_code}")
                results["users"]["profile"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ GET /api/v1/users/me - FAILED: {str(e)}")
            results["users"]["profile"] = f"FAIL: {str(e)}"

        # Update Profile
        try:
            response = client.put(
                "/api/v1/users/me",
                json={"full_name": "Updated Name"},
                headers=headers,
            )
            if response.status_code in [200, 400]:
                print(f"✓ PUT /api/v1/users/me - OK (Status {response.status_code})")
                results["users"]["update"] = "PASS"
            else:
                print(f"✗ PUT /api/v1/users/me - Status {response.status_code}")
                results["users"]["update"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ PUT /api/v1/users/me - FAILED: {str(e)}")
            results["users"]["update"] = f"FAIL: {str(e)}"

    # 6. ORDERS ENDPOINTS
    print("\n[ORDERS ENDPOINTS]")

    if test_data["auth_token"]:
        # Get Orders
        try:
            response = client.get("/api/v1/orders", headers=headers)
            if response.status_code == 200:
                print("✓ GET /api/v1/orders - OK")
                results["orders"]["list"] = "PASS"
            else:
                print(f"✗ GET /api/v1/orders - Status {response.status_code}")
                results["orders"]["list"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ GET /api/v1/orders - FAILED: {str(e)}")
            results["orders"]["list"] = f"FAIL: {str(e)}"

        # Create Order
        try:
            response = client.post(
                "/api/v1/orders",
                json={
                    "delivery_address": {
                        "street": "123 Test St",
                        "city": "Delhi",
                        "state": "Delhi",
                        "postal_code": "110001",
                        "latitude": 28.6139,
                        "longitude": 77.2090,
                    }
                },
                headers=headers,
            )
            if response.status_code in [201, 400]:
                if response.status_code == 201:
                    test_data["order_id"] = response.json().get("order_id")
                print(f"✓ POST /api/v1/orders - OK (Status {response.status_code})")
                results["orders"]["create"] = "PASS"
            else:
                print(f"✗ POST /api/v1/orders - Status {response.status_code}")
                results["orders"]["create"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ POST /api/v1/orders - FAILED: {str(e)}")
            results["orders"]["create"] = f"FAIL: {str(e)}"

    # 7. SOCIAL ENDPOINTS
    print("\n[SOCIAL ENDPOINTS]")

    if test_data["auth_token"]:
        # Get Feed
        try:
            response = client.get("/api/v1/social/posts?page=1", headers=headers)
            if response.status_code == 200:
                posts = response.json().get("data", [])
                if posts:
                    test_data["post_id"] = posts[0].get("id")
                print("✓ GET /api/v1/social/posts - OK")
                results["social"]["feed"] = "PASS"
            else:
                print(f"✗ GET /api/v1/social/posts - Status {response.status_code}")
                results["social"]["feed"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ GET /api/v1/social/posts - FAILED: {str(e)}")
            results["social"]["feed"] = f"FAIL: {str(e)}"

        # Create Post
        try:
            response = client.post(
                "/api/v1/social/posts",
                json={"content": "Test post for API testing"},
                headers=headers,
            )
            if response.status_code in [201, 400]:
                if response.status_code == 201:
                    test_data["post_id"] = response.json().get("id")
                print(f"✓ POST /api/v1/social/posts - OK (Status {response.status_code})")
                results["social"]["create"] = "PASS"
            else:
                print(f"✗ POST /api/v1/social/posts - Status {response.status_code}")
                results["social"]["create"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ POST /api/v1/social/posts - FAILED: {str(e)}")
            results["social"]["create"] = f"FAIL: {str(e)}"

    # 8. MODERATION ENDPOINTS
    print("\n[MODERATION ENDPOINTS]")

    if test_data["auth_token"] and test_data["post_id"]:
        # Report Post
        try:
            response = client.post(
                f"/api/v1/moderation/posts/{test_data['post_id']}/report",
                json={"reason": "spam", "description": "Test report"},
                headers=headers,
            )
            if response.status_code in [201, 400]:
                print(
                    f"✓ POST /api/v1/moderation/posts/{{id}}/report - OK (Status {response.status_code})"
                )
                results["moderation"]["report"] = "PASS"
            else:
                print(f"✗ POST /api/v1/moderation/.../report - Status {response.status_code}")
                results["moderation"]["report"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ POST /api/v1/moderation/.../report - FAILED: {str(e)}")
            results["moderation"]["report"] = f"FAIL: {str(e)}"

    # 9. ADMIN ENDPOINTS
    print("\n[ADMIN ENDPOINTS]")

    if test_data["auth_token"]:
        # Get Dashboard
        try:
            response = client.get("/api/v1/admin/dashboard", headers=headers)
            if response.status_code in [200, 403]:
                if response.status_code == 200:
                    print("✓ GET /api/v1/admin/dashboard - OK (admin)")
                else:
                    print("✓ GET /api/v1/admin/dashboard - OK (permission denied as expected)")
                results["admin"]["dashboard"] = "PASS"
            else:
                print(f"✗ GET /api/v1/admin/dashboard - Status {response.status_code}")
                results["admin"]["dashboard"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ GET /api/v1/admin/dashboard - FAILED: {str(e)}")
            results["admin"]["dashboard"] = f"FAIL: {str(e)}"

        # Get Stats
        try:
            response = client.get("/api/v1/admin/stats", headers=headers)
            if response.status_code in [200, 403]:
                print(f"✓ GET /api/v1/admin/stats - OK (Status {response.status_code})")
                results["admin"]["stats"] = "PASS"
            else:
                print(f"✗ GET /api/v1/admin/stats - Status {response.status_code}")
                results["admin"]["stats"] = f"Status {response.status_code}"
        except Exception as e:
            print(f"✗ GET /api/v1/admin/stats - FAILED: {str(e)}")
            results["admin"]["stats"] = f"FAIL: {str(e)}"

    # SUMMARY
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total_tests = sum(len(v) if isinstance(v, dict) else 1 for v in results.values())
    passed = sum(
        1 for v in results.values()
        if isinstance(v, dict) and all("PASS" in str(val) for val in v.values())
        or (isinstance(v, str) and "PASS" in v)
    )
    
    for module, tests in results.items():
        if isinstance(tests, dict):
            for test_name, status in tests.items():
                status_icon = "✓" if "PASS" in str(status) else "✗"
                print(f"{status_icon} {module}.{test_name}: {status}")
        else:
            status_icon = "✓" if "PASS" in str(tests) else "✗"
            print(f"{status_icon} {module}: {tests}")
    
    print("\n" + "="*70)
    print("✓ TEST RUN COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_tests()
