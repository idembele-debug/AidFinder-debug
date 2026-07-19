import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, Trash2, Calendar, AlertTriangle, RefreshCw } from 'lucide-react'
import dashboardService from '@/src/services/dashboardService'
import { ListSkeleton } from '@/src/components/dashboard/SkeletonLoader'
import EmptyState from '@/src/components/dashboard/EmptyState'
import { Button } from '@/components/ui/button'
import { useToast } from '@/src/contexts/ToastContext'
import { formatLocalDateTime } from '@/src/utils/date'

export default function HistoriquePage() {
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const navigate = useNavigate()
  const { showToast } = useToast()

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await dashboardService.getHistory()
      setConversations(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const handleDelete = async (e, historyId) => {
    e.stopPropagation()
    if (!window.confirm('Voulez-vous vraiment supprimer cette conversation ?')) return

    setDeletingId(historyId)
    try {
      await dashboardService.deleteHistory(historyId)
      setConversations((prev) => prev.filter((c) => c.historique_id !== historyId))
      showToast('Discussion supprimée avec succès', 'success')
    } catch {
      showToast('Impossible de supprimer la discussion', 'error')
    } finally {
      setDeletingId(null)
    }
  }

  const handleRowClick = (historyId) => {
    navigate(`/dashboard/discussion/${historyId}`)
  }

  if (loading) {
    return (
      <div className="flex-1 px-4 py-6 sm:px-8 sm:py-8 space-y-6">
        <div className="space-y-2">
          <div className="h-8 w-48 bg-muted animate-pulse rounded-md" />
          <div className="h-4 w-72 bg-muted animate-pulse rounded-md" />
        </div>
        <ListSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
        <div className="rounded-full bg-destructive/10 p-3 text-destructive">
          <AlertTriangle className="size-6" />
        </div>
        <h3 className="mt-4 text-base font-bold text-foreground">Erreur de chargement</h3>
        <p className="mt-2 text-sm text-muted-foreground max-w-sm">
          Impossible de récupérer l'historique de vos discussions. Veuillez réessayer.
        </p>
        <Button onClick={fetchHistory} className="mt-4 bg-brand hover:bg-brand-hover text-brand-foreground">
          <RefreshCw className="mr-2 size-4" /> Réessayer
        </Button>
      </div>
    )
  }

  return (
    <div className="flex-1 px-4 py-6 sm:px-8 sm:py-8 space-y-6">
      <div className="border-b border-border/60 pb-4">
        <h1 className="flex items-center gap-2 text-xl font-bold text-foreground sm:text-2xl">
          <MessageSquare className="size-6 text-brand" />
          Historique des discussions
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Retrouvez et poursuivez toutes vos discussions passées avec notre assistant IA.
        </p>
      </div>

      <div className="space-y-3">
        {conversations.length === 0 ? (
          <EmptyState
            title="Aucune conversation"
            description="Démarrez une nouvelle discussion pour commencer à poser vos questions."
            icon={MessageSquare}
          />
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.historique_id}
              onClick={() => handleRowClick(conv.historique_id)}
              className="group cursor-pointer rounded-xl border border-border/60 bg-card p-4 shadow-xs transition-all duration-300 hover:border-border hover:shadow-md hover:bg-muted/10 w-full overflow-hidden"
            >
              {/* Layout : conteneur principal sans overflow caché */}
              <div className="flex items-start gap-3 min-w-0">
                {/* Contenu textuel — min-w-0 garantit que truncate fonctionne */}
                <div className="min-w-0 flex-1 space-y-1">
                  <h4 className="truncate text-sm font-bold text-foreground group-hover:text-brand transition-colors duration-200">
                    {conv.titre_resume || 'Discussion sans titre'}
                  </h4>

                  <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                    <Calendar className="size-3 shrink-0" />
                    <span className="truncate">{formatLocalDateTime(conv.date_derniere_activite)}</span>
                  </div>

                  <p className="truncate text-xs text-muted-foreground">
                    {conv.dernier_message || 'Pas encore de message.'}
                  </p>
                </div>

                {/* Bouton Supprimer — shrink-0 empêche le rétrécissement/débordement */}
                <div className="shrink-0">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => handleDelete(e, conv.historique_id)}
                    disabled={deletingId === conv.historique_id}
                    className="size-8 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors duration-200"
                    aria-label="Supprimer la conversation"
                  >
                    {deletingId === conv.historique_id ? (
                      <RefreshCw className="size-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="size-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
