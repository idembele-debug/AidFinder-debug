import { Globe, RefreshCw, Play, CheckCircle, XCircle, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import useAdminSources from '@/src/hooks/useAdminSources'
import { AdminCardSkeleton } from '@/src/components/admin/AdminSkeletons'
import AdminEmptyState from '@/src/components/admin/AdminEmptyState'
import AdminErrorState from '@/src/components/admin/AdminErrorState'

function FiabiliteBadge({ fiabilite }) {
  const colorMap = {
    'haute': 'bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-950 dark:text-emerald-400 dark:ring-emerald-500/30',
    'moyenne': 'bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-950 dark:text-amber-400 dark:ring-amber-500/30',
    'faible': 'bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-950 dark:text-red-400 dark:ring-red-500/30',
  }
  const key = fiabilite?.toLowerCase() || 'faible'
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-semibold ring-1 ${colorMap[key] || colorMap['faible']}`}>
      {fiabilite || '—'}
    </span>
  )
}

function StatutBadge({ statut }) {
  const isOk = statut === 'actif' || statut === 'ok'
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold ring-1 ${isOk ? 'bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-950 dark:text-emerald-400 dark:ring-emerald-500/30' : 'bg-muted text-muted-foreground ring-border'}`}>
      {isOk ? <CheckCircle className="size-3" /> : <XCircle className="size-3" />}
      {statut || '—'}
    </span>
  )
}

/**
 * Page Sources (Admin)
 */
export default function AdminSources() {
  const { sources, loading, error, refresh, runScraping, scrapingId } = useAdminSources()

  const formatDate = (d) =>
    d ? new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'

  return (
    <div className="flex-1 bg-muted/20 px-4 py-6 sm:px-6 lg:px-8 lg:py-8 space-y-6">
      {/* En-tête */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-foreground sm:text-2xl">
            <Globe className="size-6 text-brand" />
            Gestion des sources
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {sources.length} source{sources.length !== 1 ? 's' : ''} configurée{sources.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button onClick={refresh} variant="outline" size="sm" className="gap-2">
          <RefreshCw className="size-4" /> Actualiser
        </Button>
      </div>

      {/* Contenu */}
      {loading ? (
        <AdminCardSkeleton count={6} />
      ) : error ? (
        <AdminErrorState description="Impossible de charger les sources." onRetry={refresh} />
      ) : sources.length === 0 ? (
        <AdminEmptyState
          icon={Globe}
          title="Aucune source configurée"
          description="Aucune source de données n'est encore configurée."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sources.map((source) => (
            <div
              key={source.source_id}
              className="rounded-xl border border-border/60 bg-card p-5 shadow-sm transition-all duration-200 hover:shadow-md space-y-4"
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <h3 className="font-bold text-foreground truncate">{source.nom}</h3>
                  {source.url && (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-brand hover:underline truncate block mt-0.5"
                    >
                      {source.url}
                    </a>
                  )}
                </div>
                <StatutBadge statut={source.statut} />
              </div>

              {/* Infos */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-muted/30 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Fiabilité</p>
                  <div className="mt-1">
                    <FiabiliteBadge fiabilite={source.fiabilite} />
                  </div>
                </div>
                <div className="rounded-lg bg-muted/30 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Aides</p>
                  <p className="mt-1 text-lg font-bold text-foreground">{source.nombre_aides ?? 0}</p>
                </div>
              </div>

              {/* Dernier scraping */}
              <div className="flex items-center gap-2 rounded-lg bg-muted/20 px-3 py-2 text-xs text-muted-foreground">
                <Clock className="size-3.5 shrink-0" />
                <span>
                  Dernier scraping :{' '}
                  <span className="font-semibold text-foreground">{formatDate(source.dernier_scraping)}</span>
                </span>
              </div>

              {/* Bouton Scraping */}
              <Button
                onClick={() => runScraping(source.source_id)}
                disabled={scrapingId === source.source_id}
                className="w-full bg-brand hover:bg-brand-hover text-brand-foreground gap-2"
                size="sm"
              >
                {scrapingId === source.source_id ? (
                  <>
                    <RefreshCw className="size-4 animate-spin" />
                    Scraping en cours…
                  </>
                ) : (
                  <>
                    <Play className="size-4" />
                    Relancer le scraping
                  </>
                )}
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
