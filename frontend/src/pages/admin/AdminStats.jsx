import { BarChart2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import useAdminStats from '@/src/hooks/useAdminStats'
import AdminErrorState from '@/src/components/admin/AdminErrorState'

function BarChartCard({ title, subtitle, items, color = 'var(--color-brand)', unit = '' }) {
  if (!items || items.length === 0) return (
    <div className="rounded-xl border border-border/60 bg-card p-6 shadow-sm">
      <h3 className="mb-1 text-base font-bold text-foreground">{title}</h3>
      {subtitle && <p className="mb-4 text-xs text-muted-foreground">{subtitle}</p>}
      <p className="py-8 text-center text-sm text-muted-foreground">Aucune donnée disponible.</p>
    </div>
  )

  const max = Math.max(1, ...items.map((i) => i.total))

  return (
    <div className="rounded-xl border border-border/60 bg-card p-6 shadow-sm">
      <h3 className="mb-1 text-base font-bold text-foreground">{title}</h3>
      {subtitle && <p className="mb-4 text-xs text-muted-foreground">{subtitle}</p>}
      <div className="space-y-2.5">
        {items.slice(0, 10).map((item) => (
          <div key={item.label} className="flex items-center gap-3">
            <span className="w-36 truncate text-right text-xs text-muted-foreground shrink-0">{item.label}</span>
            <div className="flex-1 h-6 rounded-full bg-muted/40 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 flex items-center justify-end pr-2"
                style={{
                  width: `${Math.max(5, (item.total / max) * 100)}%`,
                  backgroundColor: color,
                }}
              >
                {item.total > 0 && (
                  <span className="text-[10px] font-bold text-brand-foreground">{item.total}{unit}</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function LineChartCard({ title, subtitle, items, color = 'var(--color-brand)' }) {
  if (!items || items.length === 0) return (
    <div className="rounded-xl border border-border/60 bg-card p-6 shadow-sm">
      <h3 className="mb-1 text-base font-bold text-foreground">{title}</h3>
      {subtitle && <p className="mb-4 text-xs text-muted-foreground">{subtitle}</p>}
      <p className="py-8 text-center text-sm text-muted-foreground">Aucune donnée disponible.</p>
    </div>
  )

  const maxVal = Math.max(1, ...items.map((i) => i.total))
  const width = 500
  const height = 120
  const padding = 10
  const pts = items.map((item, i) => ({
    x: padding + (i / Math.max(1, items.length - 1)) * (width - padding * 2),
    y: height - padding - ((item.total) / maxVal) * (height - padding * 2),
    total: item.total,
    date: item.date,
  }))
  const pathD = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const fillD = `${pathD} L ${pts[pts.length - 1]?.x} ${height} L ${pts[0]?.x} ${height} Z`

  const totalSum = items.reduce((acc, i) => acc + i.total, 0)
  const avg = Math.round(totalSum / Math.max(1, items.length))

  return (
    <div className="rounded-xl border border-border/60 bg-card p-6 shadow-sm">
      <div className="flex items-start justify-between mb-1">
        <h3 className="text-base font-bold text-foreground">{title}</h3>
        <div className="text-right">
          <p className="text-2xl font-bold text-foreground">{totalSum}</p>
          <p className="text-[10px] text-muted-foreground">total · moy. {avg}/jour</p>
        </div>
      </div>
      {subtitle && <p className="mb-4 text-xs text-muted-foreground">{subtitle}</p>}

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-32" preserveAspectRatio="none">
        <defs>
          <linearGradient id={`fill-${title}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.25" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={fillD} fill={`url(#fill-${title})`} />
        <path d={pathD} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        {pts.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="4" fill="var(--color-card)" stroke={color} strokeWidth="2" />
          </g>
        ))}
      </svg>

      {items.length > 1 && (
        <div className="flex justify-between text-[10px] text-muted-foreground mt-2">
          <span>{items[0].date}</span>
          <span>{items[items.length - 1].date}</span>
        </div>
      )}
    </div>
  )
}

/**
 * Page Statistiques (Admin)
 */
export default function AdminStats() {
  const { stats, loading, error, refresh } = useAdminStats()

  if (loading) {
    return (
      <div className="flex-1 bg-muted/20 px-4 py-6 sm:px-6 lg:px-8 lg:py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-7 w-48 bg-muted animate-pulse rounded-md" />
            <div className="h-4 w-64 bg-muted animate-pulse rounded-md" />
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-64 rounded-xl border border-border bg-card animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 bg-muted/20 flex items-center justify-center">
        <AdminErrorState description="Impossible de charger les statistiques." onRetry={refresh} />
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="flex-1 bg-muted/20 px-4 py-6 sm:px-6 lg:px-8 lg:py-8 space-y-6">
      {/* En-tête */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-foreground sm:text-2xl">
            <BarChart2 className="size-6 text-brand" />
            Statistiques
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Analyses et évolutions de la plateforme
          </p>
        </div>
        <Button onClick={refresh} variant="outline" size="sm" className="gap-2">
          <RefreshCw className="size-4" /> Actualiser
        </Button>
      </div>

      {/* Graphiques d'évolution */}
      <div className="grid gap-6 lg:grid-cols-2">
        <LineChartCard
          title="Évolution des utilisateurs"
          subtitle="Inscriptions sur les 30 derniers jours"
          items={stats.evolution_utilisateurs}
          color="var(--color-brand)"
        />
        <LineChartCard
          title="Évolution des conversations"
          subtitle="Discussions sur les 30 derniers jours"
          items={stats.evolution_conversations}
          color="var(--color-brand)"
        />
        <LineChartCard
          title="Évolution des exports PDF"
          subtitle="Exports générés sur les 30 derniers jours"
          items={stats.evolution_exports_pdf}
          color="var(--color-brand)"
        />
      </div>

      {/* Graphiques en barres */}
      <div className="grid gap-6 lg:grid-cols-2">
        <BarChartCard
          title="Aides par catégorie"
          subtitle="Répartition des aides par type"
          items={stats.aides_par_categorie}
          color="#10b981"
        />
        <BarChartCard
          title="Aides par région"
          subtitle="Distribution géographique des aides"
          items={stats.aides_par_region}
          color="#0ea5e9"
        />
      </div>

      {/* Sources les plus utilisées */}
      <BarChartCard
        title="Sources les plus actives"
        subtitle="Classement par nombre d'aides indexées"
        items={stats.sources_les_plus_utilisees}
        color="#a855f7"
      />
    </div>
  )
}
