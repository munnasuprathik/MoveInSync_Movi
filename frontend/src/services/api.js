import axios from 'axios'

const API_BASE_URL = 'http://localhost:5005/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Stops API
export const stopsAPI = {
  getAll: () => api.get('/stops/'),
  getById: (id) => api.get(`/stops/${id}`),
  create: (data) => api.post('/stops/', data),
  update: (id, data, updatedBy = 1) => api.put(`/stops/${id}`, data, { params: { updated_by: updatedBy } }),
  delete: (id, deletedBy) => api.delete(`/stops/${id}`, { params: { deleted_by: deletedBy } }),
}

// Paths API
export const pathsAPI = {
  getAll: () => api.get('/paths/'),
  getById: (id) => api.get(`/paths/${id}`),
  getStops: (id) => api.get(`/paths/${id}/stops`),
  create: (data) => api.post('/paths/', data),
  update: (id, data, updatedBy = 1) => api.put(`/paths/${id}`, data, { params: { updated_by: updatedBy } }),
  delete: (id, deletedBy) => api.delete(`/paths/${id}`, { params: { deleted_by: deletedBy } }),
}

// Routes API
export const routesAPI = {
  getAll: () => api.get('/routes/'),
  getById: (id) => api.get(`/routes/${id}`),
  getByPath: (pathId) => api.get(`/routes/by-path/${pathId}`),
  create: (data) => api.post('/routes/', data),
  update: (id, data, updatedBy = 1) => api.put(`/routes/${id}`, data, { params: { updated_by: updatedBy } }),
  delete: (id, deletedBy) => api.delete(`/routes/${id}`, { params: { deleted_by: deletedBy } }),
}

// Vehicles API
export const vehiclesAPI = {
  getAll: () => api.get('/vehicles/'),
  getUnassigned: () => api.get('/vehicles/unassigned'),
  getById: (id) => api.get(`/vehicles/${id}`),
  create: (data) => api.post('/vehicles/', data),
  update: (id, data, updatedBy = 1) => api.put(`/vehicles/${id}`, data, { params: { updated_by: updatedBy } }),
  delete: (id, deletedBy) => api.delete(`/vehicles/${id}`, { params: { deleted_by: deletedBy } }),
}

// Drivers API
export const driversAPI = {
  getAll: () => api.get('/drivers/'),
  getById: (id) => api.get(`/drivers/${id}`),
  create: (data) => api.post('/drivers/', data),
  update: (id, data, updatedBy = 1) => api.put(`/drivers/${id}`, data, { params: { updated_by: updatedBy } }),
  delete: (id, deletedBy) => api.delete(`/drivers/${id}`, { params: { deleted_by: deletedBy } }),
}

// Trips API
export const tripsAPI = {
  getAll: () => api.get('/trips/'),
  getById: (id) => api.get(`/trips/${id}`),
  getByName: (name) => api.get(`/trips/by-name/${name}`),
  create: (data) => api.post('/trips/', data),
  update: (id, data, updatedBy = 1) => api.put(`/trips/${id}`, data, { params: { updated_by: updatedBy } }),
  delete: (id, deletedBy) => api.delete(`/trips/${id}`, { params: { deleted_by: deletedBy } }),
}

// Deployments API
export const deploymentsAPI = {
  getAll: () => api.get('/deployments/'),
  getById: (id) => api.get(`/deployments/${id}`),
  getByTrip: (tripId) => api.get(`/deployments/by-trip/${tripId}`),
  create: (data) => api.post('/deployments/', data),
  update: (id, data, updatedBy = 1) => api.put(`/deployments/${id}`, data, { params: { updated_by: updatedBy } }),
  delete: (id, deletedBy) => api.delete(`/deployments/${id}`, { params: { deleted_by: deletedBy } }),
}

// Agent Chat API (LangGraph agent)
export const agentAPI = {
  chat: (message, currentPage, sessionId) => 
    api.post('/chat', {
      message,
      current_page: currentPage,
      session_id: sessionId
    }),
  uploadImage: (file, message, currentPage, sessionId) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('message', message)
    formData.append('current_page', currentPage)
    formData.append('session_id', sessionId)
    return api.post('/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}

// Chatbot API (old simple chatbot - kept for backward compatibility)
export const chatbotAPI = {
  chat: (messages, temperature = 0.7, maxTokens = 500) => 
    api.post('/chatbot/', {
      messages,
      temperature,
      max_tokens: maxTokens
    }),
}


export default api

