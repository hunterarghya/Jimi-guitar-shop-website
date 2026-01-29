// API Configuration and utility functions
const API_BASE_URL = "http://localhost:8000";

// Token management
const TokenManager = {
  // Determine if we're in admin or user context
  getContext() {
    const path = window.location.pathname;
    return path.includes("/admin") ? "admin" : "user";
  },

  getStorageKey(key) {
    const context = this.getContext();
    return `${context}_${key}`;
  },

  setTokens(accessToken, refreshToken) {
    const context = this.getContext();
    // Use sessionStorage for admin (cleared on tab close)
    // Use localStorage for user (persists)
    const storage = context === "admin" ? sessionStorage : localStorage;
    storage.setItem(this.getStorageKey("accessToken"), accessToken);
    storage.setItem(this.getStorageKey("refreshToken"), refreshToken);
  },

  getAccessToken() {
    const context = this.getContext();
    const storage = context === "admin" ? sessionStorage : localStorage;
    return storage.getItem(this.getStorageKey("accessToken"));
  },

  getRefreshToken() {
    const context = this.getContext();
    const storage = context === "admin" ? sessionStorage : localStorage;
    return storage.getItem(this.getStorageKey("refreshToken"));
  },

  getUserId() {
    const token = this.getAccessToken();
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.sub;
    } catch (e) {
      return null;
    }
  },

  isAdmin() {
    const token = this.getAccessToken();
    if (!token) return false;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.is_admin === true;
    } catch (e) {
      return false;
    }
  },

  clear() {
    const context = this.getContext();
    const storage = context === "admin" ? sessionStorage : localStorage;
    storage.removeItem(this.getStorageKey("accessToken"));
    storage.removeItem(this.getStorageKey("refreshToken"));
  },
};

// API Helper
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Add authorization header
  const token = TokenManager.getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Token expired, try to refresh
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return apiCall(endpoint, options);
      } else {
        window.location.href = window.location.pathname.includes("/admin")
          ? "/admin/login.html"
          : "/user/login.html";
        return null;
      }
    }

    if (!response.ok) {
      try {
        const error = await response.json();
        throw new Error(error.detail || `API Error: ${response.status}`);
      } catch (parseError) {
        throw new Error(`API Error: ${response.status}`);
      }
    }

    try {
      return await response.json();
    } catch (parseError) {
      console.error("Failed to parse response JSON:", parseError);
      console.error("Response text:", await response.text());
      throw new Error("Invalid response format from server");
    }
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

async function refreshAccessToken() {
  const refreshToken = TokenManager.getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      TokenManager.setTokens(data.access_token, data.refresh_token);
      return true;
    }
    return false;
  } catch (error) {
    console.error("Token refresh failed:", error);
    return false;
  }
}

// Auth APIs
const AuthAPI = {
  async register(firstName, lastName, email, password, confirmPassword) {
    return apiCall("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        confirm_password: confirmPassword,
      }),
    });
  },

  async login(email, password) {
    return apiCall("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async requestOTP(email) {
    return apiCall("/api/v1/auth/login-otp/request", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  async verifyOTP(email, otp) {
    return apiCall("/api/v1/auth/login-otp/verify", {
      method: "POST",
      body: JSON.stringify({ email, otp }),
    });
  },

  async logout() {
    const accessToken = TokenManager.getAccessToken();
    const refreshToken = TokenManager.getRefreshToken();

    try {
      await apiCall("/api/v1/auth/logout", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          refresh_token: refreshToken,
        },
      });
    } catch (e) {
      console.error("Logout API error:", e);
    }

    TokenManager.clear();
  },
};

// User APIs
const UserAPI = {
  async getProfile() {
    return apiCall("/api/v1/users/profile");
  },

  async updateProfile(firstName, lastName, phone) {
    return apiCall("/api/v1/users/profile", {
      method: "PUT",
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        phone,
      }),
    });
  },

  async getUserProfile(userId) {
    return apiCall(`/api/v1/users/${userId}`);
  },
};

// Product APIs
const ProductAPI = {
  async listProducts(filterObj) {
    const params = new URLSearchParams();
    if (filterObj.category) params.append("category", filterObj.category);
    if (filterObj.min_price !== null && filterObj.min_price !== undefined)
      params.append("min_price", filterObj.min_price);
    if (filterObj.max_price !== null && filterObj.max_price !== undefined)
      params.append("max_price", filterObj.max_price);
    if (filterObj.sort_by) params.append("sort_by", filterObj.sort_by);
    if (filterObj.sort_order) params.append("sort_order", filterObj.sort_order);
    const page = filterObj.page || 1;
    const pageSize = filterObj.page_size || 20;
    params.append("page", page);
    params.append("page_size", pageSize);

    return apiCall(`/api/v1/products?${params.toString()}`);
  },

  async getProduct(productId) {
    return apiCall(`/api/v1/products/${productId}`);
  },

  async searchProducts(query, limit = 10) {
    return apiCall(
      `/api/v1/products/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    );
  },

  async createProduct(data) {
    return apiCall("/api/v1/products", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateProduct(productId, data) {
    return apiCall(`/api/v1/products/${productId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async deleteProduct(productId) {
    return apiCall(`/api/v1/products/${productId}`, {
      method: "DELETE",
    });
  },
};

// Cart APIs
const CartAPI = {
  async getCart() {
    return apiCall("/api/v1/cart");
  },

  async addToCart(productId, quantity) {
    return apiCall("/api/v1/cart/items", {
      method: "POST",
      body: JSON.stringify({
        product_id: productId,
        quantity,
      }),
    });
  },

  async updateCartItem(productId, quantity) {
    return apiCall(`/api/v1/cart/items/${productId}`, {
      method: "PUT",
      body: JSON.stringify({ quantity }),
    });
  },

  async removeFromCart(productId) {
    return apiCall(`/api/v1/cart/items/${productId}`, {
      method: "DELETE",
    });
  },

  async clearCart() {
    return apiCall("/api/v1/cart/clear", {
      method: "POST",
    });
  },
};

// Order APIs
const OrderAPI = {
  async createOrder(items) {
    return apiCall("/api/v1/orders", {
      method: "POST",
      body: JSON.stringify({
        items: items.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
          price: item.price,
        })),
      }),
    });
  },

  async verifyPayment(orderId, paymentId, signature) {
    return apiCall("/api/v1/orders/verify-payment", {
      method: "POST",
      body: JSON.stringify({
        order_id: orderId,
        razorpay_payment_id: paymentId,
        razorpay_signature: signature,
      }),
    });
  },

  async getOrders(page = 1, pageSize = 10) {
    return apiCall(`/api/v1/orders?page=${page}&page_size=${pageSize}`);
  },

  async getOrderDetails(orderId) {
    return apiCall(`/api/v1/orders/${orderId}`);
  },
};

// Social APIs
const SocialAPI = {
  async getFeed(page = 1, pageSize = 20) {
    return apiCall(`/api/v1/posts?page=${page}&page_size=${pageSize}`);
  },

  async getPost(postId) {
    return apiCall(`/api/v1/posts/${postId}`);
  },

  async createPost(caption, images = []) {
    return apiCall("/api/v1/posts", {
      method: "POST",
      body: JSON.stringify({
        caption,
        images,
      }),
    });
  },

  async updatePost(postId, caption, images = []) {
    return apiCall(`/api/v1/posts/${postId}`, {
      method: "PUT",
      body: JSON.stringify({
        caption,
        images,
      }),
    });
  },

  async deletePost(postId) {
    return apiCall(`/api/v1/posts/${postId}`, {
      method: "DELETE",
    });
  },

  async likePost(postId) {
    return apiCall(`/api/v1/posts/${postId}/like`, {
      method: "POST",
    });
  },

  async unlikePost(postId) {
    return apiCall(`/api/v1/posts/${postId}/like`, {
      method: "DELETE",
    });
  },

  async savePost(postId) {
    return apiCall(`/api/v1/posts/${postId}/save`, {
      method: "POST",
    });
  },

  async unsavePost(postId) {
    return apiCall(`/api/v1/posts/${postId}/save`, {
      method: "DELETE",
    });
  },

  async addComment(postId, text) {
    return apiCall(`/api/v1/posts/${postId}/comments`, {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  },

  async getComments(postId, page = 1, pageSize = 50) {
    return apiCall(
      `/api/v1/posts/${postId}/comments?page=${page}&page_size=${pageSize}`,
    );
  },

  async getLikes(postId, page = 1, pageSize = 50) {
    return apiCall(
      `/api/v1/posts/${postId}/likes?page=${page}&page_size=${pageSize}`,
    );
  },

  async getUserPosts(userId, page = 1, pageSize = 20) {
    return apiCall(
      `/api/v1/posts/users/${userId}/posts?page=${page}&page_size=${pageSize}`,
    );
  },

  async getSavedPosts(userId, page = 1, pageSize = 20) {
    return apiCall(
      `/api/v1/posts/users/${userId}/saved?page=${page}&page_size=${pageSize}`,
    );
  },

  async updatePost(postId, data) {
    return apiCall(`/api/v1/posts/${postId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async reportPost(postId, reason, description) {
    return apiCall(`/api/v1/moderation/posts/${postId}/report`, {
      method: "POST",
      body: JSON.stringify({
        reason,
        description,
      }),
    });
  },
};

// Chatbot API
const ChatbotAPI = {
  async chat(message, conversationId = null) {
    return apiCall("/api/v1/chatbot/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });
  },
};

// Admin APIs
const AdminAPI = {
  async getDashboard() {
    return apiCall("/api/v1/admin/dashboard");
  },

  async getStats() {
    return apiCall("/api/v1/admin/stats");
  },

  async createDiscount(code, discountPercent, maxUses, expiryDate) {
    return apiCall("/api/v1/admin/discounts", {
      method: "POST",
      body: JSON.stringify({
        code,
        discount_percent: discountPercent,
        max_uses: maxUses,
        expiry_date: expiryDate,
      }),
    });
  },

  async getDiscounts() {
    return apiCall("/api/v1/admin/discounts");
  },

  async updateDiscount(code, discountPercent, maxUses, expiryDate) {
    return apiCall(`/api/v1/admin/discounts/${code}`, {
      method: "PUT",
      body: JSON.stringify({
        discount_percent: discountPercent,
        max_uses: maxUses,
        expiry_date: expiryDate,
      }),
    });
  },

  async deleteDiscount(code) {
    return apiCall(`/api/v1/admin/discounts/${code}`, {
      method: "DELETE",
    });
  },

  async getPendingPosts(page = 1, pageSize = 20) {
    return apiCall(
      `/api/v1/moderation/pending?page=${page}&page_size=${pageSize}`,
    );
  },

  async approvePost(postId) {
    return apiCall(`/api/v1/moderation/posts/${postId}/approve`, {
      method: "PUT",
      body: JSON.stringify({ action: "approve" }),
    });
  },

  async rejectPost(postId, rejectionReason) {
    return apiCall(`/api/v1/moderation/posts/${postId}/reject`, {
      method: "PUT",
      body: JSON.stringify({
        action: "reject",
        rejection_reason: rejectionReason,
      }),
    });
  },

  async getModerationStats() {
    return apiCall("/api/v1/moderation/statistics");
  },
};

// Utility functions
function showError(message) {
  alert(`Error: ${message}`);
}

function showSuccess(message) {
  alert(`Success: ${message}`);
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString() + " " + date.toLocaleTimeString();
}

function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(amount);
}
