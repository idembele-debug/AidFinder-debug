import { Sparkles, RefreshCw, AlertTriangle } from 'lucide-react'
import useRecommendations from '@/src/hooks/useRecommendations'
import RecommendationSection from '@/src/components/dashboard/RecommendationSection'
import { RecommendationsSkeleton } from '@/src/components/dashboard/SkeletonLoader'
import { Button } from '@/components/ui/button'

export default function AidesRecommandeesPage() {
  const { recommendations, loading, error, refresh } = useRecommendations()

  if (loading) {
    return (
      <div className="flex-1 px-4 py-6 sm:px-8 sm:py-8 space-y-6">
        <div className="space-y-2">
          <div className="h-8 w-48 bg-muted animate-pulse rounded-md" />
          <div className="h-4 w-72 bg-muted animate-pulse rounded-md" />
        </div>
        <RecommendationsSkeleton />
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
          Impossible de récupérer vos recommandations d'aides. Veuillez réessayer.
        </p>
        <Button onClick={refresh} className="mt-4 bg-brand hover:bg-brand-hover text-brand-foreground">
          <RefreshCw className="mr-2 size-4" /> Réessayer
        </Button>
      </div>
    )
  }

  return (
    <div className="flex-1 px-4 py-6 sm:px-8 sm:py-8 space-y-6">
      <div className="border-b border-border/60 pb-4">
        <h1 className="flex items-center gap-2 text-xl font-bold text-foreground sm:text-2xl">
          <Sparkles className="size-6 text-amber-500 fill-amber-500" />
          Aides recommandées
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Voici les aides publiques et dispositifs d'accompagnement de l'État sélectionnés pour vous.
        </p>
      </div>

      <div className="pt-2">
        <RecommendationSection recommendations={recommendations} />
      </div>
    </div>
  )
}
