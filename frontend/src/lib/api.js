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

export async function loginUser(username, password) {
  const response = await axios.post(`${API_BASE_URL}/auth/login`, {
    username,
    password,
  });

  const { access_token, user } = response.data;
  localStorage.setItem('campusmind_token', access_token);
  localStorage.setItem('campusmind_user', JSON.stringify(user));
  return user;
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

// Phase 3 & 4 Institutional API v1 Helpers
const API_V1_URL = '/api/v1';

export async function fetchCurrentTerm() {
  const response = await axios.get(`${API_V1_URL}/academics/terms/current`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchCourseOfferings() {
  const response = await axios.get(`${API_V1_URL}/academics/offerings`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchStudentAttendance(enrollmentNo) {
  const response = await axios.get(`${API_V1_URL}/attendance/student/${enrollmentNo}`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function recordAttendance(offeringId, records) {
  const response = await axios.post(
    `${API_V1_URL}/attendance/offering/${offeringId}`,
    { records },
    { headers: getAuthHeader() }
  );
  return response.data;
}

export async function fetchStudentResults(enrollmentNo) {
  const response = await axios.get(`${API_V1_URL}/assessments/student/${enrollmentNo}`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function createAssessment(data) {
  const response = await axios.post(`${API_V1_URL}/assessments`, data, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function recordGrades(assessmentId, grades) {
  const response = await axios.post(
    `${API_V1_URL}/assessments/${assessmentId}/grades`,
    { grades },
    { headers: getAuthHeader() }
  );
  return response.data;
}

export async function fetchAnnouncements() {
  const response = await axios.get(`${API_V1_URL}/announcements`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function createAnnouncement(data) {
  const response = await axios.post(`${API_V1_URL}/announcements`, data, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchCampusEvents() {
  const response = await axios.get(`${API_V1_URL}/events`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function createCampusEvent(data) {
  const response = await axios.post(`${API_V1_URL}/events`, data, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function registerForEvent(eventId) {
  const response = await axios.post(`${API_V1_URL}/events/${eventId}/register`, {}, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchKnowledgeDocuments() {
  const response = await axios.get(`${API_V1_URL}/knowledge`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function createKnowledgeDocument(data) {
  const response = await axios.post(`${API_V1_URL}/knowledge`, data, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function deactivateKnowledgeDocument(docId) {
  const response = await axios.post(`${API_V1_URL}/knowledge/${docId}/deactivate`, {}, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function activateKnowledgeDocument(docId) {
  const response = await axios.post(`${API_V1_URL}/knowledge/${docId}/activate`, {}, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function triggerVectorSync() {
  const response = await axios.post(`${API_V1_URL}/knowledge/sync`, {}, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function performUnifiedSearch(query) {
  const response = await axios.get(`${API_V1_URL}/search`, {
    params: { q: query },
    headers: getAuthHeader(),
  });
  return response.data;
}

// Phase 5 Academic Analytics API Helpers
export async function fetchStudentAnalyticsMe() {
  const response = await axios.get(`${API_V1_URL}/analytics/student/me`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchStudentAttendanceAnalytics() {
  const response = await axios.get(`${API_V1_URL}/analytics/student/me/attendance`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchStudentPerformanceAnalytics() {
  const response = await axios.get(`${API_V1_URL}/analytics/student/me/performance`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchStudentRiskAnalytics() {
  const response = await axios.get(`${API_V1_URL}/analytics/student/me/risk`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchStudentRecommendations() {
  const response = await axios.get(`${API_V1_URL}/analytics/student/me/recommendations`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchFacultyOfferingAnalytics(offeringId) {
  const response = await axios.get(`${API_V1_URL}/analytics/faculty/offerings/${offeringId}`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchAdminAnalyticsOverview() {
  const response = await axios.get(`${API_V1_URL}/analytics/admin/overview`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchAdminDepartmentAnalytics(departmentId) {
  const response = await axios.get(`${API_V1_URL}/analytics/admin/departments/${departmentId}`, {
    headers: getAuthHeader(),
  });
  return response.data;
}

export async function fetchAdminProgramAnalytics(programId) {
  const response = await axios.get(`${API_V1_URL}/analytics/admin/programs/${programId}`, {
    headers: getAuthHeader(),
  });
  return response.data;
}
