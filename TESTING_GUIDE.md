# QUICK TEST GUIDE - Verify All Fixes

## Prerequisites

- App is running: `http://localhost:8000`
- Frontend accessible at: `http://localhost`

## Test 1: Authentication & Admin Access

### Step 1: Register an Admin User

```
Email: testadmin@example.com
Password: TestAdmin123!@
First Name: Test
Last Name: Admin
```

Navigate to: `http://localhost/admin/login.html`

### Step 2: Make User an Admin (Database)

```bash
docker exec jimi_postgres psql -U postgres -d jimi -c "UPDATE users SET is_admin = true WHERE email = 'testadmin@example.com';"
```

### Step 3: Login as Admin

- Use credentials from Step 1
- Should see Admin Dashboard
- Should see Product List loaded successfully (no 401 errors)

**Expected Result:** ✅ Dashboard loads with product list visible

---

## Test 2: Product Sorting

### Step 1: Create Products (via Admin Dashboard)

- Click "Products" section
- Add products with different prices:
  - Product A: ₹500
  - Product B: ₹2000
  - Product C: ₹1000

### Step 2: Test Sorting

- Go to marketplace (User Dashboard)
- Look for "Sort by" dropdown
- Try each option:
  - **Low to High** → Should show: 500, 1000, 2000
  - **High to Low** → Should show: 2000, 1000, 500
  - **Newest** → Should show most recently created first

**Expected Result:** ✅ Products reorder correctly when sort option changes

---

## Test 3: User Posts Filtering

### Step 1: Create Posts

- Login as a regular user
- Go to "Social" section
- Create 2-3 posts

### Step 2: View User Posts

- Go to "Profile" section
- Look for "My Posts" subsection

**Expected Result:** ✅ Only your posts appear (not other users' posts)

---

## Test 4: Multi-User Scenario (Optional)

### Step 1: Open Two Browsers

- Browser 1: Login as User A (regular user)
- Browser 2: Login as User B (admin)

### Step 2: Verify Token Isolation

- Each user should see their own profile
- Each user's posts should be filtered correctly

**Expected Result:** ✅ No data bleeding between users (may require separate browsers if using same browser/tabs)

---

## Test 5: API Endpoints

### Test Authentication Working

```bash
# Create test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"verify@example.com","password":"Verify123!@","first_name":"Test","last_name":"User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"verify@example.com","password":"Verify123!@"}' > token.json

# Extract token (using jq or similar)
TOKEN=$(jq -r '.access_token' token.json)

# Test authenticated endpoint
curl -X GET http://localhost:8000/api/v1/users/profile \
  -H "Authorization: Bearer $TOKEN"

# Should return your profile (not 401)
```

### Test Sorting Parameters

```bash
curl -X GET "http://localhost:8000/api/v1/products?sort_by=price&sort_order=asc&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# Should return products sorted by price ascending
```

**Expected Result:** ✅ 200 OK responses, no 401 errors

---

## Troubleshooting

### Still seeing 401 errors?

1. Check if app restarted properly:
   ```bash
   docker compose restart app
   ```
2. Check app logs:
   ```bash
   docker logs jimi_app --tail 50
   ```
3. Verify token is valid:
   ```bash
   # Token should have format: header.payload.signature
   echo $TOKEN | cut -d'.' -f2 | base64 -d | jq .
   ```

### Products not sorting?

1. Check if dropdown value is being read
2. Open browser DevTools (F12)
3. Check Network tab - sort_by parameter should be in URL
4. Check Console for JavaScript errors

### User posts not showing?

1. Make sure you're logged in (check navbar shows your name)
2. Create at least one post in Social section
3. Go to Profile section
4. Check browser console for errors

---

## All Tests Completed?

When all tests pass, the platform is ready for further development!

Last Updated: 2026-01-29
Status: ✅ Ready for Testing
