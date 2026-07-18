import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import EmptyState from './EmptyState'
import { Bookmark, ExternalLink } from 'lucide-react'
import dashboardService from '@/src/services/dashboardService'

/**
 * Section "Dernières aides consultées" du dashboard.
 * Accepte les données via la prop recentAids (fournies par useDashboard).
 * Enregistre la consultation lors du clic sur "Consulter".
 */
export default function RecentAidsSection({ recentAids = [] }) {
  const handleConsult = async (aid) => {
    if (!aid?.url_officielle) return
    try {
      await dashboardService.recordAidConsultation(aid.aide_id)
    } catch {
      // Ignorer l'erreur d'enregistrement — l'ouverture du lien reste prioritaire
    } finally {
      window.open(aid.url_officielle, '_blank', 'noopener,noreferrer')
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    try {
      return new Date(dateStr).toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  if (!recentAids || recentAids.length === 0) {
    return (
      <EmptyState
        title="Aucune aide consultée"
        description="Les aides d'État que vous consultez s'afficheront ici."
        icon={Bookmark}
      />
    )
  }

  return (
    <div className="space-y-3">
      {recentAids.map((aid) => {
        const imageSrc =
          aid.image_url ||
          'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=100&auto=format&fit=crop&q=60'
        const categoryName = aid.categorie || aid.type_aide

        return (
          <Card
            key={aid.aide_id}
            className="border-border/60 bg-card shadow-xs transition-all duration-200 hover:border-border hover:bg-muted/30"
          >
            <CardContent className="flex items-center gap-3 p-3">
              {/* Thumbnail */}
              <div className="relative size-12 shrink-0 overflow-hidden rounded-lg bg-muted">
                <img src={imageSrc} alt={aid.titre} className="size-full object-cover" />
              </div>

              {/* Info */}
              <div className="min-w-0 flex-1 space-y-0.5">
                <h4 className="truncate text-xs font-bold text-foreground">{aid.titre}</h4>
                <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground">
                  {categoryName && (
                    <span className="font-semibold text-brand">{categoryName}</span>
                  )}
                  {aid.date_consultation && (
                    <span>• Consulté le {formatDate(aid.date_consultation)}</span>
                  )}
                </div>
              </div>

              {/* Button */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleConsult(aid)}
                className="shrink-0 h-8 text-[11px] font-semibold text-brand border-brand-border hover:bg-brand-light hover:border-brand transition-colors duration-200"
                disabled={!aid.url_officielle}
              >
                Consulter
                <ExternalLink className="ml-1 size-3" />
              </Button>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
