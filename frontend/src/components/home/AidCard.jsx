import { Link } from 'react-router-dom'
import { ArrowUpRight, MapPin, Tag } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { getAidImageUrl } from '@/src/utils/aids'
import homeService from '@/src/services/home'

const PLACEHOLDER_GRADIENT = 'bg-gradient-to-br from-brand-border to-brand-light/50'

/** Carte d'aide réutilisable (dernières aides, résultats de recherche). */
export default function AidCard({ aide }) {
  const imageUrl = getAidImageUrl(aide.image_url)
  const externalUrl = aide.url_officielle

  const handleConsult = async (event) => {
    if (!externalUrl) {
      return
    }
    event.preventDefault()
    try {
      await homeService.recordAidConsultation(aide.aide_id)
    } catch {
      // Les visiteurs non connectés peuvent consulter le lien sans suivi utilisateur.
    } finally {
      window.open(externalUrl, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <Card className="group overflow-hidden border-border/60 py-0 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md">
      <div className={`relative aspect-[16/10] overflow-hidden ${!imageUrl ? PLACEHOLDER_GRADIENT : ''}`}>
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={aide.titre}
            className="size-full object-cover transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex size-full items-center justify-center">
            <Tag className="size-10 text-brand/40" />
          </div>
        )}
        {aide.type_aide && (
          <span className="absolute right-3 top-3 rounded-full bg-background/90 px-2.5 py-1 text-xs font-medium text-foreground shadow-sm backdrop-blur-sm">
            {aide.type_aide}
          </span>
        )}
      </div>

      <CardContent className="flex flex-1 flex-col gap-3 p-5">
        <h3 className="line-clamp-2 font-semibold leading-snug text-foreground">
          {aide.titre}
        </h3>

        {aide.description && (
          <p className="line-clamp-2 text-sm leading-relaxed text-muted-foreground">
            {aide.description}
          </p>
        )}

        {aide.region_cible && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <MapPin className="size-3.5 shrink-0 text-brand" />
            <span className="line-clamp-1">{aide.region_cible}</span>
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          className="mt-auto w-full border-brand-border text-brand hover:bg-brand-light/50"
          asChild
        >
          {externalUrl ? (
            <a href={externalUrl} target="_blank" rel="noopener noreferrer" onClick={handleConsult}>
              Voir plus
              <ArrowUpRight className="size-3.5" />
            </a>
          ) : (
            <Link to="/register">
              Voir plus
              <ArrowUpRight className="size-3.5" />
            </Link>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
