import { useProfile } from '@/src/contexts/ProfileContext'
import { getProfilePhotoUrl } from '@/src/services/user'
import { Calendar } from 'lucide-react'

export default function DashboardHeader({ nom = 'Utilisateur' }) {
  const { profile } = useProfile()
  const today = new Date()
  const formattedDate = today.toLocaleDateString('fr-FR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
  const dateString = formattedDate.charAt(0).toUpperCase() + formattedDate.slice(1)

  const photoUrl = getProfilePhotoUrl(profile?.photo_profil)
  const initials = nom
    ? nom
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U'

  return (
    <div className="flex flex-col gap-4 border-b border-border/60 pb-6 sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          Bonjour, {nom} 👋
        </h1>
        <p className="text-sm text-muted-foreground sm:text-base">
          Voici les dernières aides correspondant à votre profil.
        </p>
      </div>

      <div className="flex items-center gap-3 self-start sm:self-center">
        <div className="flex flex-col items-end hidden xs:flex">
          <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <Calendar className="size-3.5" />
            {dateString}
          </span>
        </div>

        <div className="relative flex size-12 shrink-0 overflow-hidden rounded-full border border-border bg-muted shadow-xs">
          {photoUrl ? (
            <img
              src={photoUrl}
              alt={nom}
              className="aspect-square size-full object-cover"
              onError={(e) => {
                e.target.onerror = null
                e.target.style.display = 'none'
              }}
            />
          ) : (
            <div className="flex size-full items-center justify-center bg-brand text-sm font-semibold text-brand-foreground">
              {initials}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
