import axios from 'axios';

const API_BASE_URL = '/api';

// Helper to retrieve auth header
function getAuthHeader() {
  const token = localStorage.getItem('campusmind_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Add Axios response interceptor for automatic 401 token invalidation handling
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('campusmind_token');
      localStorage.removeItem('campusmind_user');
    }
    return Promise.reject(error);
  }
);


export function getStoredUser() {
  const userStr = localStorage.getItem('campusmind_user');
  return userStr ? JSON.parse(userStr) : null;
}

export function logoutUser() {
  localStorage.removeItem('campusmind_token');
  localStorage.removeItem('campusmind_user');
}

export async function loginUser(username, password, role) {
  const response = await axios.post(`${API_BASE_URL}/auth/login`, {
    username,
    password,
    role,
  });

  const { access_token, user } = response.data;
  localStorage.setItem('campusmind_token', access_token);
  localStorage.setItem('campusmind_user', JSON.stringify(user));
  return user;
}

export async function switchUserRole(currentUsername, newRole) {
  return await loginUser(currentUsername, 'password123', newRole);
}

export async function sendChatMessage(message) {
  const response = await axios.post(
    `${API_BASE_URL}/chat`,
    { message },
    { headers: getAuthHeader() }
  );
  return response.data;
}

export async function sendFeedback(queryId, isPositive) {
  const response = await axios.post(
    `${API_BASE_URL}/chat/feedback`,
    { query_id: queryId, is_positive: isPositive },
    { headers: getAuthHeader() }
  );
  return response.data;
}

export async function fetchAdminStats() {
  const response = await axios.get(`${API_BASE_URL}/admin/stats`, {
    headers: getAuthHeader(),
  });
  return response.data;
}
