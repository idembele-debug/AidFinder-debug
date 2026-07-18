import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useProfile } from '@/src/contexts/ProfileContext'
import useDashboard from '@/src/hooks/useDashboard'

// Composants Dashboard
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import ProfileCard from '@/src/components/dashboard/ProfileCard'
import StatsCards from '@/src/components/dashboard/StatsCards'
import RecommendationSection from '@/src/components/dashboard/RecommendationSection'
import HistorySection from '@/src/components/dashboard/HistorySection'
import RecentAidsSection from '@/src/components/dashboard/RecentAidsSection'
import QuickActions from '@/src/components/dashboard/QuickActions'
import SkeletonLoader from '@/src/components/dashboard/SkeletonLoader'

// UI & Icons
import { Button } from '@/components/ui/button'
import { Bot, Sparkles } from 'lucide-react'

export default function DashbordUI() {
  const { profile } = useProfile()
  const { data, loading, error, refresh } = useDashboard()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  // Scroll fluide vers une section ciblée (?scroll=history ou ?scroll=recommendations)
  useEffect(() => {
    const scrollTarget = searchParams.get('scroll')
    if (scrollTarget) {
      const timer = setTimeout(() => {
        const element = document.getElementById(scrollTarget)
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [searchParams])

  const handleStartChat = () => {
    navigate('/dashboard/discussion')
  }

  const handleContinueChat = (conv) => {
    navigate(`/dashboard/discussion/${conv.historique_id}`)
  }

  if (loading) {
    return (
      <div className="flex-1 px-4 py-8 sm:px-8 md:py-10">
        <SkeletonLoader />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
        <div className="rounded-full bg-destructive/10 p-3 text-destructive">
          <Bot className="size-6" />
        </div>
        <h3 className="mt-4 text-base font-bold text-foreground">Erreur de chargement</h3>
        <p className="mt-2 text-sm text-muted-foreground max-w-sm">
          Impossible de se connecter au serveur backend. Veuillez vérifier que le serveur est démarré.
        </p>
        <Button onClick={refresh} className="mt-4 bg-brand hover:bg-brand-hover text-brand-foreground">
          Réessayer
        </Button>
      </div>
    )
  }

  return (
    <div className="flex-1 px-4 py-6 sm:px-8 sm:py-8 space-y-8">
      {/* Header */}
      <DashboardHeader nom={data?.nom_utilisateur || profile?.nom} />

      {/* Grid Principal */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Colonne Gauche : Stats & Recommandations (2/3 de l'écran) */}
        <div className="lg:col-span-2 space-y-8">
          {/* Cartes Statistiques */}
          <StatsCards
            recherches={data?.nombre_recherches}
            conversations={data?.nombre_conversations}
            recommandations={data?.nombre_recommandations}
            pdfExportes={data?.nombre_pdf_exportes}
          />

          {/* Section Recommandations */}
          <div id="recommendations" className="space-y-4 pt-2">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-base font-bold text-foreground">
                <Sparkles className="size-5 text-amber-500 fill-amber-500" />
                Aides recommandées
              </h2>
            </div>
            <RecommendationSection recommendations={data?.aides_recommandees} />
          </div>
        </div>

        {/* Colonne Droite : Infos Profil & Actions & Historique (1/3 de l'écran) */}
        <div className="space-y-6">
          {/* Carte Profil */}
          <ProfileCard />

          {/* Actions Rapides */}
          <QuickActions
            onStartChat={handleStartChat}
          />

          {/* Historique Récent */}
          <div id="history" className="space-y-3 pt-2">
            <h3 className="text-sm font-semibold text-foreground">Historique des conversations</h3>
            <HistorySection
              conversations={data?.dernieres_conversations}
              onContinueChat={handleContinueChat}
            />
          </div>

          {/* Dernières Aides Consultées */}
          <div className="space-y-3 pt-2">
            <h3 className="text-sm font-semibold text-foreground">Dernières aides consultées</h3>
            <RecentAidsSection recentAids={data?.dernieres_aides_consultees} />
          </div>
        </div>
      </div>
    </div>
  )
}
