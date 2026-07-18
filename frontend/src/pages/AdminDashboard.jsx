import {
  Users, FileText, FolderOpen, Globe,
  MessageSquare, Download, UserCheck, UserX, RefreshCw
} from 'lucide-react'
import useAdminDashboard from '@/src/hooks/useAdminDashboard'
import useAdminStats from '@/src/hooks/useAdminStats'
import { AdminStatsSkeleton } from '@/src/components/admin/AdminSkeletons'
import AdminErrorState from '@/src/components/admin/AdminErrorState'

function StatCard({ label, value, icon: Icon, colorClass, bgClass }) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-border/60 bg-card p-5 shadow-sm transition-all duration-300 hover:shadow-md hover:-translate-y-0.5">
      <div className={`flex size-11 shrink-0 items-center justify-center rounded-xl border ${bgClass}`}>
        <Icon className={`size-5 ${colorClass}`} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-semibold text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-bold tracking-tight text-foreground">
          {value ?? '—'}
        </p>
      </div>
    </div>
  )
}

function BarChart({ items, label, color = 'var(--color-brand)' }) {
  if (!items || items.length === 0) return (
    <p className="py-8 text-center text-sm text-muted-foreground">Aucune donnée disponible.</p>
  )
  const max = Math.max(1, ...items.map((i) => i.total))
  return (
    <div className="space-y-2">
      {items.slice(0, 8).map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <span className="w-32 truncate text-xs text-muted-foreground text-right">{item.label}</span>
          <div className="flex-1 h-5 rounded-full bg-muted/50 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${Math.max(4, (item.total / max) * 100)}%`, backgroundColor: color }}
              />
          </div>
          <span className="w-8 text-xs font-bold text-foreground text-right">{item.total}</span>
        </div>
      ))}
    </div>
  )
}

function LineChart({ items, color = 'var(--color-brand)', label }) {
  if (!items || items.length === 0) return (
    <p className="py-8 text-center text-sm text-muted-foreground">Aucune donnée disponible.</p>
  )
  const maxVal = Math.max(1, ...items.map((i) => i.total))
  const width = 400
  const height = 100
  const points = items.map((item, i) => ({
    x: (i / Math.max(1, items.length - 1)) * width,
    y: height - (item.total / maxVal) * (height - 10),
    label: item.date,
    total: item.total,
  }))
  const d = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height + 20}`} className="w-full h-28">
        <defs>
          <linearGradient id={`grad-${label}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.2" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d={`${d} L ${width} ${height} L 0 ${height} Z`}
          fill={`url(#grad-${label})`}
        />
        <path d={d} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="3" fill={color} />
        ))}
      </svg>
      <div className="flex justify-between text-[9px] text-muted-foreground mt-1 px-1">
        {items.length > 1 && (
          <>
            <span>{items[0].date}</span>
            <span>{items[items.length - 1].date}</span>
          </>
        )}
      </div>
    </div>
  )
}

/**
 * Dashboard Administrateur — affiche les 8 statistiques globales + graphiques.
 */
export default function AdminDashboard() {
  const { data, loading, error, refresh } = useAdminDashboard()
  const { stats, loading: statsLoading } = useAdminStats()

  if (loading) {
    return (
      <div className="flex-1 bg-muted/20 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <div className="mb-8 space-y-2">
          <div className="h-7 w-48 bg-muted animate-pulse rounded-md" />
          <div className="h-4 w-64 bg-muted animate-pulse rounded-md" />
        </div>
        <AdminStatsSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 bg-muted/20 flex items-center justify-center">
        <AdminErrorState
          description="Impossible de charger les données du tableau de bord."
          onRetry={refresh}
        />
      </div>
    )
  }

  const statCards = [
    {
      label: 'Utilisateurs',
      value: data?.total_utilisateurs,
      icon: Users,
      colorClass: 'text-blue-600 dark:text-blue-400',
      bgClass: 'bg-blue-50 border-blue-100 dark:bg-blue-950 dark:border-blue-900',
    },
    {
      label: 'Aides publiées',
      value: data?.total_aides,
      icon: FileText,
      colorClass: 'text-emerald-600 dark:text-emerald-400',
      bgClass: 'bg-emerald-50 border-emerald-100 dark:bg-emerald-950 dark:border-emerald-900',
    },
    {
      label: 'Catégories',
      value: data?.total_categories,
      icon: FolderOpen,
      colorClass: 'text-violet-600 dark:text-violet-400',
      bgClass: 'bg-violet-50 border-violet-100 dark:bg-violet-950 dark:border-violet-900',
    },
    {
      label: 'Sources',
      value: data?.total_sources,
      icon: Globe,
      colorClass: 'text-sky-600 dark:text-sky-400',
      bgClass: 'bg-sky-50 border-sky-100 dark:bg-sky-950 dark:border-sky-900',
    },
    {
      label: 'Conversations',
      value: data?.total_conversations,
      icon: MessageSquare,
      colorClass: 'text-orange-600 dark:text-orange-400',
      bgClass: 'bg-orange-50 border-orange-100 dark:bg-orange-950 dark:border-orange-900',
    },
    {
      label: 'PDF exportés',
      value: data?.total_pdf_exportes,
      icon: Download,
      colorClass: 'text-pink-600 dark:text-pink-400',
      bgClass: 'bg-pink-50 border-pink-100 dark:bg-pink-950 dark:border-pink-900',
    },
    {
      label: 'Comptes actifs',
      value: data?.comptes_actifs,
      icon: UserCheck,
      colorClass: 'text-green-600 dark:text-green-400',
      bgClass: 'bg-green-50 border-green-100 dark:bg-green-950 dark:border-green-900',
    },
    {
      label: 'Comptes désactivés',
      value: data?.comptes_desactives,
      icon: UserX,
      colorClass: 'text-red-600 dark:text-red-400',
      bgClass: 'bg-red-50 border-red-100 dark:bg-red-950 dark:border-red-900',
    },
  ]

  return (
    <div className="flex-1 bg-muted/20 px-4 py-6 sm:px-6 lg:px-8 lg:py-8 space-y-8">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground sm:text-2xl">Tableau de bord</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Vue globale de la plateforme AidFinder
          </p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm font-medium text-foreground shadow-sm hover:bg-muted/50 transition-colors"
        >
          <RefreshCw className="size-4" />
          <span className="hidden sm:inline">Actualiser</span>
        </button>
      </div>

      {/* Statistiques principales */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {statCards.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      {/* Graphiques */}
      {!statsLoading && stats && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Aides par catégorie */}
          <div className="rounded-xl border border-border/60 bg-card p-6 shadow-sm">
            <h3 className="mb-4 text-base font-bold text-foreground">Aides par catégorie</h3>
            <BarChart items={stats.aides_par_categorie} label="categories" color="#10b981" />
          </div>

          {/* Aides par région */}
          <div className="rounded-xl border border-border/60 bg-card p-6 shadow-sm">
            <h3 className="mb-4 text-base font-bold text-foreground">Aides par région</h3>
            <BarChart items={stats.aides_par_region} label="regions" color="#0ea5e9" />
          </div>

          {/* Évolution utilisateurs */}
          <div className="rounded-xl border border-border/60 bg-card p-6 shadow-sm">
            <h3 className="mb-1 text-base font-bold text-foreground">
              Évolution des utilisateurs
            </h3>
            <p className="mb-4 text-xs text-muted-foreground">30 derniers jours</p>
            <LineChart items={stats.evolution_utilisateurs} color="var(--color-brand)" label="users" />
          </div>

          {/* Évolution conversations */}
          <div className="rounded-xl border border-border/60 bg-card p-6 shadow-sm">
            <h3 className="mb-1 text-base font-bold text-foreground">
              Évolution des conversations
            </h3>
            <p className="mb-4 text-xs text-muted-foreground">30 derniers jours</p>
            <LineChart items={stats.evolution_conversations} color="var(--color-brand)" label="conversations" />
          </div>

          {/* Sources les plus utilisées */}
          <div className="rounded-xl border border-border/60 bg-card p-6 shadow-sm lg:col-span-2">
            <h3 className="mb-4 text-base font-bold text-foreground">Sources les plus utilisées</h3>
            <BarChart items={stats.sources_les_plus_utilisees} label="sources" color="#a855f7" />
          </div>
        </div>
      )}
    </div>
  )
}
