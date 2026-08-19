import api from './api'

/**
 * Service Administration — communique avec les routes FastAPI /admin/*
 */
export const adminService = {
  // ─── Dashboard ───────────────────────────────────────────────────────────────
  getDashboard: async () => {
    const { data } = await api.get('/admin/dashboard')
    return data
  },

  // ─── Utilisateurs ────────────────────────────────────────────────────────────
  getUsers: async () => {
    const { data } = await api.get('/admin/utilisateurs')
    return data
  },

  getUser: async (userId) => {
    const { data } = await api.get(`/admin/utilisateur/${userId}`)
    return data
  },

  updateUser: async (userId, payload) => {
    const { data } = await api.put(`/admin/utilisateur/${userId}`, payload)
    return data
  },

  activateUser: async (userId) => {
    const { data } = await api.patch(`/admin/utilisateur/${userId}/activer`)
    return data
  },

  deactivateUser: async (userId) => {
    const { data } = await api.patch(`/admin/utilisateur/${userId}/desactiver`)
    return data
  },

  deleteUser: async (userId) => {
    const { data } = await api.delete(`/admin/utilisateur/${userId}`)
    return data
  },

  getUserWarnings: async (userId) => {
    const { data } = await api.get(`/admin/utilisateur/${userId}/avertissements`)
    return data
  },

  createWarning: async (userId, payload) => {
    const { data } = await api.post(`/admin/utilisateur/${userId}/avertissements`, payload)
    return data
  },

  // ─── Aides ───────────────────────────────────────────────────────────────────
  getAides: async () => {
    const { data } = await api.get('/admin/aides')
    return data
  },

  createAide: async (payload) => {
    const { data } = await api.post('/admin/aides', payload)
    return data
  },

  updateAide: async (aideId, payload) => {
    const { data } = await api.put(`/admin/aides/${aideId}`, payload)
    return data
  },

  deleteAide: async (aideId) => {
    const { data } = await api.delete(`/admin/aides/${aideId}`)
    return data
  },

  activateAide: async (aideId) => {
    const { data } = await api.patch(`/admin/aides/${aideId}/activer`)
    return data
  },

  deactivateAide: async (aideId) => {
    const { data } = await api.patch(`/admin/aides/${aideId}/desactiver`)
    return data
  },

  // ─── Statistiques ─────────────────────────────────────────────────────────────
  getStatistics: async () => {
    const { data } = await api.get('/admin/statistiques')
    return data
  },
}

export default adminService
