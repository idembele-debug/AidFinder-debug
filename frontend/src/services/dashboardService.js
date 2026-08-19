import api from './api'

/**
 * Service Dashboard — communique avec les routes FastAPI /dashboard/*
 */
export const dashboardService = {
  /** Récupère les données consolidées de la page d'accueil du dashboard */
  getDashboard: async () => {
    const { data } = await api.get('/dashboard')
    return data
  },

  /** Récupère l'historique complet des conversations */
  getHistory: async () => {
    const { data } = await api.get('/dashboard/history')
    return data
  },

  /** Récupère la liste des recommandations d'aides adaptées à l'utilisateur */
  getRecommendations: async () => {
    const { data } = await api.get('/dashboard/recommendations')
    return data
  },

  /** Récupère les dernières aides consultées */
  getRecentAids: async () => {
    const { data } = await api.get('/dashboard/recent-aids')
    return data
  },

  /** Récupère les statistiques détaillées de l'utilisateur */
  getStats: async () => {
    const { data } = await api.get('/dashboard/stats')
    return data
  },

  /** Récupère les détails (messages) d'une discussion */
  getHistoryDetail: async (historyId) => {
    const { data } = await api.get(`/dashboard/history/${historyId}`)
    return data
  },

  /** Supprime une discussion par son ID */
  deleteHistory: async (historyId) => {
    const { data } = await api.delete(`/dashboard/history/${historyId}`)
    return data
  },

  /** Envoie un message de discussion (crée ou continue) — NON-STREAMING (conservé) */
  sendChatMessage: async (message, historiqueId = null) => {
    const { data } = await api.post('/dashboard/chat', {
      message,
      historique_id: historiqueId,
    })
    return data
  },

  /**
   * Envoie un message en streaming SSE via fetch natif.
   *
   * Axios ne supporte pas nativement le streaming SSE dans le navigateur.
   * On utilise donc fetch + ReadableStream.
   *
   * @param {string} message - Message de l'utilisateur
   * @param {number|null} historiqueId - ID de la conversation existante (null = nouvelle)
   * @param {object} callbacks
   * @param {function} callbacks.onChunk  - Appelé à chaque chunk texte : (text: string) => void
   * @param {function} callbacks.onDone   - Appelé avec les métadonnées finales : (data: object) => void
   * @param {function} callbacks.onError  - Appelé en cas d'erreur : (err: Error) => void
   * @returns {AbortController} — Permet d'annuler le stream si besoin
   */
  streamChatMessage: (message, historiqueId = null, { onChunk, onDone, onError } = {}) => {
    const controller = new AbortController()

    const run = async () => {
      try {
        // Construire l'URL en utilisant le même mécanisme que l'instance axios
        const { getApiBaseUrl } = await import('@/src/config/env')
        const baseUrl = getApiBaseUrl()
        const token = localStorage.getItem('access_token')

        const response = await fetch(`${baseUrl}/dashboard/chat/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            message,
            historique_id: historiqueId,
          }),
          signal: controller.signal,
        })

        // Gestion des erreurs HTTP (401, 500, etc.)
        if (!response.ok) {
          if (response.status === 401) {
            localStorage.removeItem('access_token')
            localStorage.removeItem('user')
            if (!window.location.pathname.startsWith('/login')) {
              window.location.href = '/login'
            }
            return
          }
          throw new Error(`Erreur serveur : ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Les événements SSE sont séparés par "\n\n"
          const parts = buffer.split('\n\n')
          // Le dernier élément est potentiellement incomplet — on le remet dans le buffer
          buffer = parts.pop() ?? ''

          for (const part of parts) {
            const line = part.trim()
            if (!line.startsWith('data:')) continue

            const jsonStr = line.slice('data:'.length).trim()
            if (!jsonStr) continue

            let event
            try {
              event = JSON.parse(jsonStr)
            } catch {
              // Ligne SSE malformée — on ignore
              continue
            }

            if (event.type === 'chunk' && typeof event.data === 'string') {
              onChunk?.(event.data)
            } else if (event.type === 'done' && event.data) {
              onDone?.(event.data)
            }
          }
        }
      } catch (err) {
        // AbortError = annulation volontaire, ne pas remonter comme erreur
        if (err?.name !== 'AbortError') {
          onError?.(err)
        }
      }
    }

    run()
    return controller
  },

  recordAidConsultation: async (aideId) => {
    const { data } = await api.post(`/api/home/aids/${aideId}/consultation`)
    return data
  },

  recordChatConsultation: async (historiqueId, aideId) => {
    const { data } = await api.post(`/dashboard/chat/${historiqueId}/consultation/${aideId}`)
    return data
  },
}

export default dashboardService
