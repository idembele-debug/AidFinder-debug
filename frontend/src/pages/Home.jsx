import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowDown,
  ArrowRight,
  Database,
  FileDown,
  Search,
  Sparkles,
  UserPlus,
  UserRound,
  MessageSquare,
  FileText,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import AidCard from '@/src/components/home/AidCard'
import AidCardSkeleton from '@/src/components/home/AidCardSkeleton'
import CategoryCard from '@/src/components/home/CategoryCard'
import CategoryCardSkeleton from '@/src/components/home/CategoryCardSkeleton'
import HomeSearch from '@/src/components/home/HomeSearch'
import heroImage from '@/src/assets/images/image_finder.png'
import homeService from '@/src/services/home'
import { formatFrenchDate } from '@/src/utils/aids'

const BRAND = 'bg-brand hover:bg-brand-hover'

const WHY_FEATURES = [
  {
    icon: Search,
    title: 'Recherche intelligente',
    description:
      'Notre moteur analyse des centaines d\'aides pour ne retenir que celles pertinentes pour vous.',
  },
  {
    icon: Database,
    title: 'Centralisation des aides',
    description:
      'Toutes les subventions nationales et régionales réunies en un seul endroit fiable.',
  },
  {
    icon: Sparkles,
    title: 'Recommandations personnalisées',
    description:
      'L\'IA croise votre profil avec les critères d\'éligibilité pour des résultats sur mesure.',
  },
  {
    icon: FileDown,
    title: 'Export PDF',
    description:
      'Conservez et partagez vos recommandations dans un document clair et professionnel.',
  },
]

const HOW_IT_WORKS = [
  { icon: UserPlus, label: 'Créer un compte' },
  { icon: UserRound, label: 'Compléter son profil' },
  { icon: MessageSquare, label: 'Discuter avec l\'IA' },
  { icon: Sparkles, label: 'Recevoir ses recommandations' },
  { icon: FileText, label: 'Exporter en PDF' },
]

function SectionHeader({ badge, title, description, id, dark = false }) {
  return (
    <div id={id} className="mx-auto mb-12 max-w-2xl text-center">
      {badge && (
        <span className={`mb-3 inline-block rounded-full px-4 py-1.5 text-xs font-medium ${
          dark ? 'bg-white/10 text-white/90' : 'bg-brand-light text-brand'
        }`}>
          {badge}
        </span>
      )}
      <h2 className={`text-2xl font-bold tracking-tight sm:text-3xl ${
        dark ? 'text-white' : 'text-foreground'
      }`}>
        {title}
      </h2>
      {description && (
        <p className={`mt-3 ${dark ? 'text-white/70' : 'text-muted-foreground'}`}>
          {description}
        </p>
      )}
    </div>
  )
}

/** Page d'accueil — plateforme de recherche de subventions */
export default function Home() {
  const [latestAids, setLatestAids] = useState([])
  const [categories, setCategories] = useState([])
  const [stats, setStats] = useState(null)
  const [aidsLoading, setAidsLoading] = useState(true)
  const [categoriesLoading, setCategoriesLoading] = useState(true)
  const [statsLoading, setStatsLoading] = useState(true)

  useEffect(() => {
    homeService
      .getLatestAids()
      .then(setLatestAids)
      .catch(() => setLatestAids([]))
      .finally(() => setAidsLoading(false))
  }, [])

  useEffect(() => {
    homeService
      .getCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
      .finally(() => setCategoriesLoading(false))
  }, [])

  useEffect(() => {
    homeService
      .getStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setStatsLoading(false))
  }, [])

  return (
    <div className="overflow-hidden">
      {/* 1 — Hero */}
      <section className="relative bg-gradient-to-b from-brand-light/50 via-background to-background">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-16 sm:px-6 md:py-24 lg:grid-cols-2 lg:gap-16 lg:px-8">
          <div className="order-2 animate-in fade-in slide-in-from-bottom-4 duration-700 lg:order-1">
            <span className="mb-4 inline-block rounded-full bg-brand-light px-4 py-1.5 text-xs font-medium text-brand">
              Plateforme d&apos;aides financières
            </span>
            <h1 className="text-3xl font-bold leading-tight tracking-tight text-foreground sm:text-4xl lg:text-[2.75rem] lg:leading-[1.15]">
              Trouver les aides auxquelles vous êtes{' '}
              <span className="text-brand">réellement éligible</span>
            </h1>
            <p className="mt-5 max-w-lg text-base leading-relaxed text-muted-foreground sm:text-lg">
              AidFinder centralise les subventions, analyse votre profil et vous
              guide vers les aides qui correspondent vraiment à votre situation.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button size="lg" className={BRAND} asChild>
                <Link to="/register">
                  Commencer
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <a href="#latest-aids">Découvrir les aides</a>
              </Button>
            </div>
          </div>

          <div className="order-1 flex justify-center animate-in fade-in duration-700 lg:order-2">
            <img
              src={heroImage}
              alt="Illustration AidFinder — recherche d'aides financières"
              className="w-full max-w-md rounded-2xl object-contain drop-shadow-xl lg:max-w-lg"
            />
          </div>
        </div>
      </section>

      {/* 2 — Pourquoi AidFinder */}
      <section className="border-y border-border/60 bg-muted/30 py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <SectionHeader
            badge="Pourquoi AidFinder ?"
            title="Une plateforme conçue pour vous faire gagner du temps"
            description="Centralisez, personnalisez et exportez vos résultats en toute confiance."
          />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {WHY_FEATURES.map(({ icon: Icon, title, description }) => (
              <div
                key={title}
                className="rounded-xl border border-border/60 bg-card p-6 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="mb-4 flex size-11 items-center justify-center rounded-xl bg-brand-light">
                  <Icon className="size-5 text-brand" />
                </div>
                <h3 className="font-semibold text-foreground">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3 — Dernières aides */}
      <section className="py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <SectionHeader
            id="latest-aids"
            badge="Nouveautés"
            title="Dernières aides disponibles"
            description="Les subventions les plus récemment ajoutées à notre base."
          />

          {aidsLoading ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <AidCardSkeleton key={i} />
              ))}
            </div>
          ) : latestAids.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border bg-muted/30 px-6 py-16 text-center">
              <p className="text-muted-foreground">
                Aucune aide disponible pour le moment. Revenez bientôt !
              </p>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {latestAids.map((aide) => (
                <AidCard key={aide.aide_id} aide={aide} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* 4 — Catégories */}
      <section className="border-y border-border/60 bg-muted/30 py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <SectionHeader
            badge="Catégories"
            title="Explorez par profil"
            description="Retrouvez les aides adaptées à votre situation en un coup d'œil."
          />

          {categoriesLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <CategoryCardSkeleton key={i} />
              ))}
            </div>
          ) : categories.length === 0 ? (
            <p className="text-center text-muted-foreground">
              Aucune catégorie disponible pour le moment.
            </p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {categories.map((category) => (
                <CategoryCard key={category.id} category={category} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* 5 — Comment ça fonctionne */}
      <section className="py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <SectionHeader
            badge="Processus"
            title="Comment ça fonctionne"
            description="De l'inscription à l'export PDF, en cinq étapes simples."
          />

          {/* Mobile — timeline verticale */}
          <div className="flex flex-col items-center gap-2 md:hidden">
            {HOW_IT_WORKS.map(({ icon: Icon, label }, index) => (
              <div key={label} className="flex flex-col items-center">
                <div className="flex size-14 items-center justify-center rounded-2xl border border-brand-border bg-brand-light shadow-sm">
                  <Icon className="size-6 text-brand" />
                </div>
                <p className="mt-3 max-w-[12rem] text-center text-sm font-medium text-foreground">
                  {label}
                </p>
                {index < HOW_IT_WORKS.length - 1 && (
                  <ArrowDown className="my-3 size-5 text-brand/40" />
                )}
              </div>
            ))}
          </div>

          {/* Desktop — timeline horizontale */}
          <div className="hidden items-start md:flex">
            {HOW_IT_WORKS.map(({ icon: Icon, label }, index) => (
              <div key={label} className="flex flex-1 items-start">
                <div className="flex flex-col items-center">
                  <div className="flex size-14 items-center justify-center rounded-2xl border border-brand-border bg-brand-light shadow-sm transition-shadow hover:shadow-md">
                    <Icon className="size-6 text-brand" />
                  </div>
                  <p className="mt-3 max-w-[8.5rem] text-center text-sm font-medium text-foreground">
                    {label}
                  </p>
                </div>
                {index < HOW_IT_WORKS.length - 1 && (
                  <div className="mt-7 flex flex-1 items-center px-2">
                    <div className="h-px w-full bg-gradient-to-r from-brand/40 to-brand/10" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6 — Statistiques */}
      <section className="border-y border-border/60 bg-[#1a2332] py-16 text-white md:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <SectionHeader
            badge="En chiffres"
            title="Une base de données fiable et à jour"
            description="Des données consolidées depuis des sources officielles."
            dark
          />

          <div className="grid gap-6 sm:grid-cols-3">
            {statsLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="rounded-xl bg-white/5 p-8">
                  <Skeleton className="mx-auto h-10 w-24 bg-white/10" />
                  <Skeleton className="mx-auto mt-3 h-4 w-32 bg-white/10" />
                </div>
              ))
            ) : (
              <>
                <StatCard
                  value={stats?.total_aides ?? 0}
                  label="Aides référencées"
                />
                <StatCard
                  value={stats?.total_sources ?? 0}
                  label="Sources officielles"
                />
                <StatCard
                  value={formatFrenchDate(stats?.derniere_mise_a_jour)}
                  label="Dernière mise à jour"
                  isText
                />
              </>
            )}
          </div>
        </div>
      </section>

      {/* 7 — Recherche */}
      <section id="search" className="py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <SectionHeader
            badge="Recherche"
            title="Trouvez une aide en quelques secondes"
            description="Tapez un mot-clé pour explorer instantanément notre catalogue."
          />
          <HomeSearch />
        </div>
      </section>

      {/* CTA final */}
      <section className="border-t border-border/60 bg-muted/30 py-16 md:py-20">
        <div className="mx-auto max-w-6xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
            Prêt à découvrir vos aides ?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
            Créez votre compte gratuitement et laissez notre assistant IA
            identifier les subventions qui vous correspondent.
          </p>
          <Button size="lg" className={`mt-8 ${BRAND}`} asChild>
            <Link to="/register">
              Créer un compte
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  )
}

function StatCard({ value, label, isText = false }) {
  return (
    <div className="animate-in fade-in zoom-in-95 rounded-xl border border-white/10 bg-white/5 p-8 text-center duration-700">
      <p
        className={`font-bold text-brand ${isText ? 'text-lg sm:text-xl' : 'text-4xl sm:text-5xl'}`}
      >
        {value}
      </p>
      <p className="mt-2 text-sm text-white/70">{label}</p>
    </div>
  )
}
