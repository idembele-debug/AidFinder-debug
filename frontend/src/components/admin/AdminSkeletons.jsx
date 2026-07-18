/**
 * Composants Skeleton pour l'espace admin.
 * Utilisés pendant le chargement des données.
 */

export function AdminStatsSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <div key={i} className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5 shadow-sm animate-pulse">
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-lg bg-muted shrink-0" />
            <div className="h-4 w-24 bg-muted rounded" />
          </div>
          <div className="h-8 w-16 bg-muted rounded" />
        </div>
      ))}
    </div>
  )
}

export function AdminTableSkeleton({ cols = 5, rows = 6 }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-4 border-b border-border/60 bg-muted/30 px-6 py-4">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-4 w-24 bg-muted rounded animate-pulse flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 border-b border-border/60 px-6 py-4 last:border-0 animate-pulse"
        >
          <div className="size-10 rounded-full bg-muted shrink-0" />
          {Array.from({ length: cols - 1 }).map((_, j) => (
            <div key={j} className="h-4 bg-muted rounded flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

export function AdminCardSkeleton({ count = 4 }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-xl border border-border bg-card p-5 shadow-sm animate-pulse space-y-3">
          <div className="h-5 w-3/4 bg-muted rounded" />
          <div className="h-4 w-1/2 bg-muted rounded" />
          <div className="h-4 w-2/3 bg-muted rounded" />
          <div className="flex gap-2 pt-2">
            <div className="h-8 flex-1 bg-muted rounded-lg" />
            <div className="h-8 w-8 bg-muted rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  )
}
