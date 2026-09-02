import { Skeleton } from '@/components/ui/skeleton'

/**
 * Squelette d'un message de conversation (chargement initial).
 */
export function ChatMessageSkeleton() {
  return (
    <div className="space-y-6 py-2 animate-pulse">
      {/* Bot message */}
      <div className="flex items-start gap-3">
        <Skeleton className="size-8 rounded-xl shrink-0" />
        <Skeleton className="h-14 w-2/3 rounded-2xl rounded-tl-none" />
      </div>
      {/* User message */}
      <div className="flex items-start gap-3 justify-end">
        <Skeleton className="h-10 w-1/2 rounded-2xl rounded-tr-none" />
        <Skeleton className="size-8 rounded-xl shrink-0" />
      </div>
      {/* Bot message */}
      <div className="flex items-start gap-3">
        <Skeleton className="size-8 rounded-xl shrink-0" />
        <Skeleton className="h-20 w-3/4 rounded-2xl rounded-tl-none" />
      </div>
    </div>
  )
}

/**
 * Squelette d'une carte d'aide recommandée.
 */
export function AidCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-xs">
      <Skeleton className="h-36 w-full rounded-none" />
      <div className="flex flex-1 flex-col gap-3 p-4">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-2/3" />
        <div className="space-y-1.5">
          <div className="flex justify-between">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-10" />
          </div>
          <Skeleton className="h-1.5 w-full rounded-full" />
        </div>
        <Skeleton className="mt-auto h-9 w-full rounded-lg" />
      </div>
    </div>
  )
}

export function StatsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex flex-col gap-3 rounded-xl border border-border bg-card p-6 shadow-xs">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-3 w-32" />
        </div>
      ))}
    </div>
  )
}

export function ProfileSkeleton() {
  return (
    <div className="flex flex-col gap-6 rounded-xl border border-border bg-card p-6 shadow-xs">
      <div className="flex items-center gap-4">
        <Skeleton className="size-16 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-8" />
        </div>
        <Skeleton className="h-2 w-full rounded-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-36" />
        <div className="flex flex-wrap gap-2">
          <Skeleton className="h-6 w-20 rounded-md" />
          <Skeleton className="h-6 w-24 rounded-md" />
        </div>
      </div>
      <Skeleton className="h-9 w-full rounded-lg" />
    </div>
  )
}

export function RecommendationsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex flex-col overflow-hidden rounded-xl border border-border bg-card shadow-xs">
          <Skeleton className="h-48 w-full" />
          <div className="flex flex-1 flex-col gap-3 p-5">
            <Skeleton className="h-4 w-20 rounded-full" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
            <div className="mt-auto pt-4">
              <Skeleton className="h-9 w-full rounded-lg" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function ListSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center justify-between rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3.5 w-32" />
          </div>
          <Skeleton className="h-8 w-24 rounded-lg" />
        </div>
      ))}
    </div>
  )
}

export default function SkeletonLoader() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="size-10 rounded-full" />
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <StatsSkeleton />
          <div className="space-y-4">
            <Skeleton className="h-6 w-36" />
            <RecommendationsSkeleton />
          </div>
        </div>
        <div className="space-y-6">
          <ProfileSkeleton />
          <div className="space-y-4">
            <Skeleton className="h-6 w-36" />
            <ListSkeleton />
          </div>
        </div>
      </div>
    </div>
  )
}
