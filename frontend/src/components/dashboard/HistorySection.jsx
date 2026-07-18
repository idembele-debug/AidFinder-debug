import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import EmptyState from './EmptyState'
import { History, MessageSquare, Trash2 } from 'lucide-react'
import dashboardService from '@/src/services/dashboardService'

/**
 * Section historique des conversations dans le dashboard.
 * Chaque entrée est cliquable pour ouvrir la conversation.
 * La suppression est fonctionnelle via l'icône corbeille.
 */
export default function HistorySection({ conversations = [], onContinueChat, onDelete }) {
  const navigate = useNavigate()
  const [deletingId, setDeletingId] = useState(null)
  const [localConversations, setLocalConversations] = useState(null)

  // On utilise les conversations du parent si pas de state local modifié
  const displayedConversations = localConversations ?? conversations

  if (!displayedConversations || displayedConversations.length === 0) {
    return (
      <EmptyState
        title="Aucune discussion"
        description="Vous n'avez pas encore de conversation. Cliquez sur Nouvelle discussion pour commencer."
        icon={History}
      />
    )
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const handleOpen = (conv) => {
    navigate(`/dashboard/discussion/${conv.historique_id}`)
    onContinueChat?.(conv)
  }

  const handleDelete = async (e, conv) => {
    e.stopPropagation()
    if (!window.confirm('Voulez-vous vraiment supprimer cette conversation ?')) return

    setDeletingId(conv.historique_id)
    try {
      await dashboardService.deleteHistory(conv.historique_id)
      // Mise à jour locale immédiate
      const updated = displayedConversations.filter(
        (c) => c.historique_id !== conv.historique_id
      )
      setLocalConversations(updated)
      onDelete?.(conv.historique_id)
    } catch {
      // Erreur silencieuse — l'utilisateur peut réessayer depuis l'historique complet
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-3">
      {displayedConversations.map((conv) => (
        <Card
          key={conv.historique_id}
          className="group cursor-pointer border-border/60 bg-card shadow-xs transition-all duration-200 hover:border-border hover:bg-muted/30 hover:shadow-sm"
          onClick={() => handleOpen(conv)}
        >
          <CardContent className="flex items-center justify-between gap-4 p-4">
            <div className="min-w-0 flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <MessageSquare className="size-4 shrink-0 text-brand" />
                <h4 className="truncate text-sm font-semibold text-foreground group-hover:text-brand transition-colors duration-200">
                  {conv.titre_resume || 'Discussion sans titre'}
                </h4>
              </div>
              <p className="truncate text-xs text-muted-foreground pl-6">
                {conv.dernier_message || 'Démarrée le ' + formatDate(conv.date_creation)}
              </p>
              <p className="text-[10px] text-muted-foreground pl-6">
                Activité : {formatDate(conv.date_derniere_activite || conv.date_creation)}
              </p>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => handleDelete(e, conv)}
              disabled={deletingId === conv.historique_id}
              className="shrink-0 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors duration-200"
              aria-label="Supprimer la conversation"
            >
              <Trash2 className="size-4" />
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
