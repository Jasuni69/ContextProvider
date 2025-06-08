const API_BASE_URL = '/api'

// Helper function to handle fetch requests
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  
  // Default headers
  const defaultHeaders = {
    'Content-Type': 'application/json',
  }
  
  // Add auth token if available
  const token = localStorage.getItem('token')
  if (token) {
    defaultHeaders.Authorization = `Bearer ${token}`
  }
  
  // Merge headers
  const headers = {
    ...defaultHeaders,
    ...options.headers,
  }
  
  // Make the request
  const response = await fetch(url, {
    ...options,
    headers,
  })
  
  // Handle 401 unauthorized
  if (response.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  
  // Parse JSON response
  if (response.headers.get('content-type')?.includes('application/json')) {
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.detail || `HTTP error! status: ${response.status}`)
    }
    
    return data
  }
  
  // For non-JSON responses
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  
  return response
}

// Document API
export const documentAPI = {
  upload: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiRequest('/documents/upload', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    })
  },
  
  getAll: () => apiRequest('/documents/'),
  
  delete: (id) => apiRequest(`/documents/${id}`, { method: 'DELETE' }),
  
  getById: (id) => apiRequest(`/documents/${id}`),
}

// Chat API
export const chatAPI = {
  sendMessage: (message) => apiRequest('/chat/message', {
    method: 'POST',
    body: JSON.stringify({ message }),
  }),
  
  getSessions: () => apiRequest('/chat/sessions'),
  
  createSession: () => apiRequest('/chat/sessions', { method: 'POST' }),
  
  getSession: (id) => apiRequest(`/chat/sessions/${id}`),
  
  deleteSession: (id) => apiRequest(`/chat/sessions/${id}`, { method: 'DELETE' }),
}

// User API (for future authentication)
export const userAPI = {
  login: (credentials) => apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  }),
  
  register: (userData) => apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify(userData),
  }),
  
  getProfile: () => apiRequest('/auth/me'),
  
  logout: () => apiRequest('/auth/logout', { method: 'POST' }),
}

export default { documentAPI, chatAPI, userAPI } 