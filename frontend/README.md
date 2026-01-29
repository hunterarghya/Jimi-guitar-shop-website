# Jimi Frontend - User & Admin Portal

A comprehensive plain HTML/CSS/JavaScript frontend for the Jimi music marketplace and social platform.

## 🚀 Quick Start

### Prerequisites

- Backend API running on `http://localhost:8000`
- Modern web browser

### Running the Frontend

#### **For Users:**

Open in your browser:

```
http://localhost:8000/user/login.html
```

#### **For Admin:**

Open in your browser:

```
http://localhost:8000/admin/login.html
```

#### **Main Portal:**

```
http://localhost:8000/
```

> **Note:** The frontend is served directly by the FastAPI backend on `localhost:8000`.

---

## 👥 Login Instructions

### **User Login**

Access: `http://localhost:8000/user/login.html`

#### **Option 1: Email & Password Login**

1. Click on the "Login" tab
2. Enter your email and password
3. Click "Login"

#### **Option 2: OTP Login**

1. Click "📱 OTP Login" button
2. Enter your email
3. Click "Send OTP"
4. Check your email for the 6-digit OTP
5. Enter the OTP and click "Verify"

#### **Option 3: Register New Account**

1. Click "Sign Up Here"
2. Fill in your details (First Name, Last Name, Email, Password)
3. Click "Create Account"
4. Login with your new credentials

#### **Note on Google Login:**

Google OAuth integration will be added in a future update.

---

### **Admin Login**

Access: `frontend/admin/login.html`

#### **How to Create an Admin Account:**

1. Create a user account from user login
2. Open your backend database and update the user's `is_admin` flag to `true`:
   ```sql
   UPDATE users SET is_admin = true WHERE email = 'your-email@example.com';
   ```

#### **Admin Login Flow:**

1. Go to `http://localhost:8000/admin/login.html`
2. Enter your admin email
3. Enter your password
4. Click "Login as Admin"
5. System verifies admin privileges - if not admin, login fails

---

## 📱 User Features

### **Dashboard Navigation**

Once logged in, users see a navbar with 4 tabs:

#### **1. 🏪 Marketplace**

- Browse all available musical instruments
- **Filters:**
  - Category (Guitars, Drums, Keyboards, Bass, Percussion)
  - Price range (Min/Max)
  - Sort by price (Low to High, High to Low, Newest)
- **Pagination:** Navigate through products
- **Add to Cart:** Add items to shopping cart
- **Features coming soon:** Checkout with payment gateway, location-based delivery check (10km radius)

#### **2. 📱 Social**

- **Create Posts:** Share music moments with caption and images
- **View Feed:** See all public posts from community
- **Interact with Posts:**
  - ❤️ Like posts (toggle on/off)
  - 💬 Comment on posts with replies
  - 💾 Save posts for later
  - View likes and comments count
  - Delete your own posts
- **My Posts Section:** View all your posted content
- **Saved Posts:** Access your bookmarked posts
- **Pagination:** Navigate through feed

#### **3. 👤 Profile**

- View your profile information
- **Edit Profile:**
  - First Name
  - Last Name
  - Phone Number
- View your posts history
- View your saved posts

#### **4. 🤖 Ask Jimi**

- Chat with AI assistant (coming soon)
- Ask about instruments, pricing, delivery
- Get recommendations

---

## 🔐 Admin Features

### **Dashboard Navigation**

Admin sees a sidebar with 5 sections:

#### **1. 📊 Dashboard**

- **Key Metrics:**
  - Total Revenue
  - Total Orders
  - Total Users
  - Pending Posts for Review
- **Top Products:** Revenue and sales breakdown

#### **2. 📦 Products Management**

- **View All Products** with category, price, stock
- **Add New Product:**
  - Name, Category, Price, Stock Quantity, Description
- **Edit Product** (feature available)
- **Delete Product** with confirmation

#### **3. 🚫 Post Moderation**

- Review pending posts from users
- **Actions:**
  - ✓ **Approve** - Makes post visible to all
  - ✕ **Reject** - With rejection reason
- See post details (author, caption, images, timestamp)
- Automatic pagination

#### **4. 🏷️ Discounts Management**

- **Create Discount Codes:**
  - Code name (e.g., SUMMER20)
  - Discount percentage (0-100)
  - Max uses (or unlimited)
  - Expiry date
- **View All Discounts** with details
- **Edit Discounts**
- **Delete Discounts** with confirmation

#### **5. 🛒 Orders Management**

- View all orders from customers
- See order details (Order ID, Customer, Amount, Status, Date)
- Track order status (Pending, Processing, Delivered)

---

## 🔑 Key Technical Details

### **Authentication & Security**

- **JWT Tokens:**
  - Access token stored in `localStorage` for API calls
  - Refresh token for token renewal
- **Admin Verification:**
  - Tokens contain `is_admin` flag
  - Admin login verifies this flag
  - Non-admins cannot access admin portal
- **Token Management:**
  - Automatic token refresh on expiry
  - Auto-logout on invalid/expired tokens
  - Logout clears all tokens

### **API Integration**

- All frontend calls use `shared/api.js`
- Endpoints match backend API routes
- Error handling with user-friendly messages
- Loading states for async operations

### **Data Flow**

```
User/Admin
    ↓
Frontend (HTML/JS)
    ↓
API Calls (shared/api.js)
    ↓
Backend API (localhost:8000)
    ↓
PostgreSQL / MongoDB / Redis
```

---

## 📁 File Structure

```
frontend/
├── shared/
│   └── api.js              # All API calls, token management
├── user/
│   ├── login.html          # User login/register page
│   └── dashboard.html      # User main dashboard
└── admin/
    ├── login.html          # Admin-only login
    └── dashboard.html      # Admin dashboard & management
```

---

## 🧪 Testing Workflow

### **Complete User Journey:**

1. **Register New User:**

   - Open: `http://localhost:8000/user/login.html`
   - Click "Sign up here"
   - Create account with email: `musician@example.com`

2. **Browse & Shop:**

   - Login with above credentials
   - Go to 🏪 Marketplace tab
   - Browse instruments
   - Add to cart (feature complete)

3. **Use Social Features:**

   - Click 📱 Social tab
   - Create a post with caption and image URLs
   - Like and comment on other posts
   - Save posts for later

4. **Update Profile:**

   - Click 👤 Profile tab
   - Update name and phone
   - View your posts and saved posts

5. **Logout:**
   - Click "Logout" button
   - Redirected to login page

### **Admin Workflow:**

1. **Create Admin User:**

   - First register as normal user
   - Update database: `UPDATE users SET is_admin = true WHERE email = 'admin@example.com';`

2. **Admin Login:**

   - Open: `http://localhost:8000/admin/login.html`
   - Login with admin email
   - System verifies admin access

3. **Manage Products:**

   - Go to 📦 Products section
   - Click "+ Add Product"
   - Fill details and submit

4. **Moderate Content:**

   - Go to 🚫 Moderation section
   - Review pending posts
   - Approve or reject

5. **Manage Discounts:**

   - Go to 🏷️ Discounts section
   - Create seasonal discount codes

6. **View Analytics:**
   - Dashboard shows revenue, orders, users
   - Monitor platform health

---

## 🚀 Features Implemented

### ✅ User Frontend

- [x] Login/Register with email & password
- [x] OTP-based login
- [x] Browse marketplace with filters & pagination
- [x] Create/edit/delete posts
- [x] Like/unlike posts
- [x] Comment on posts
- [x] Save/unsave posts
- [x] View user profile & posts
- [x] Update profile information
- [x] Responsive navbar navigation

### ✅ Admin Frontend

- [x] Secure admin-only login
- [x] Dashboard with KPIs
- [x] Product CRUD operations
- [x] Post moderation (approve/reject)
- [x] Discount code management
- [x] Order tracking
- [x] Sidebar navigation

### ⏳ Coming Soon

- [ ] Google OAuth integration
- [ ] Payment gateway (Razorpay) integration
- [ ] Location-based delivery (10km radius check)
- [ ] Chatbot integration
- [ ] Advanced filtering & search
- [ ] Real-time notifications
- [ ] Image upload feature
- [ ] User reviews and ratings
- [ ] Dark mode

---

## 🎨 Design Principles

- **Clean & Minimal:** Pure HTML/CSS without frameworks
- **User-Friendly:** Intuitive navigation and clear CTAs
- **Responsive:** Works on desktop (mobile optimization coming)
- **Accessible:** Semantic HTML and keyboard navigation
- **Fast:** No heavy dependencies or frameworks

---

## 🔗 Related Documentation

- Backend API: Check `/IMPLEMENTATION_GUIDE.md` for API endpoints
- Database Schema: See migration files in `/migrations/`
- Setup Guide: Refer to `/STARTUP_GUIDE.md`

---

## 💡 Notes for Development

1. **Backend Must Be Running:**

   - Start backend with `docker compose up -d`
   - API should be accessible at `http://localhost:8000`

2. **CORS Configuration:**

   - Backend CORS is configured to allow frontend requests
   - Check `app/api.py` for CORS settings

3. **Local Storage:**

   - Tokens stored in browser's `localStorage`
   - Clear browser data to test fresh login

4. **Admin Security:**

   - Admin login URL is not hidden, but access is verified via `is_admin` flag
   - Non-admin accounts cannot access admin features
   - To prevent discovery, admin URL should be communicated separately

5. **Styling:**
   - All styling is inline CSS in HTML files
   - Easy to customize colors and fonts
   - Framework migration can be done later

---

## 📞 Support & Troubleshooting

### **Common Issues:**

1. **"Cannot connect to API"**

   - Ensure backend is running: `docker ps`
   - Check if port 8000 is accessible
   - Verify API URL in `shared/api.js`

2. **"Invalid token" error**

   - Token may have expired
   - Open browser DevTools → Application → localStorage
   - Clear tokens and re-login

3. **"Admin access denied"**

   - User account doesn't have admin privileges
   - Update database with: `UPDATE users SET is_admin = true WHERE email = 'email@example.com';`
   - Re-login

4. **"CORS error"**
   - Backend CORS not configured properly
   - Check `app/api.py` middleware setup

---

## 📝 License

This frontend is part of the Jimi Platform project.

---

**Happy Coding! 🎸**
