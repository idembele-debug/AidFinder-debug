import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useProfile } from '@/src/contexts/ProfileContext'
import { getProfilePhotoUrl } from '@/src/services/user'
import { AlertCircle, CheckCircle2, UserCheck } from 'lucide-react'

export default function ProfileCard() {
  const { profile } = useProfile()

  const missing = []
  if (!profile?.nom) missing.push('Nom & Prénom')
  if (!profile?.date_naissance) missing.push('Date de naissance')
  if (!profile?.region) missing.push('Région')
  if (!profile?.niveau_etude) missing.push("Niveau d'étude")
  if (!profile?.statut_socio_pro) missing.push('Statut professionnel')
  if (profile?.situation_handicap === undefined || profile?.situation_handicap === null) {
    missing.push('Situation de handicap')
  }
  if (!profile?.photo_profil) missing.push('Photo de profil')

  const totalFields = 7
  const completedCount = totalFields - missing.length
  const progressPercent = Math.round((completedCount / totalFields) * 100)

  const photoUrl = getProfilePhotoUrl(profile?.photo_profil)
  const initials = profile?.nom
    ? profile.nom
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U'

  return (
    <Card className="border-border/60 bg-card shadow-xs">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
          <UserCheck className="size-5 text-brand" />
          Mon Profil
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Infos utilisateur */}
        <div className="flex items-center gap-3">
          <div className="relative flex size-14 shrink-0 overflow-hidden rounded-full border border-border bg-muted">
            {photoUrl ? (
              <img
                src={photoUrl}
                alt={profile?.nom}
                className="aspect-square size-full object-cover"
              />
            ) : (
              <div className="flex size-full items-center justify-center bg-brand-light text-sm font-semibold text-brand">
                {initials}
              </div>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <h4 className="truncate text-sm font-bold text-foreground">
              {profile?.nom || 'Utilisateur'}
            </h4>
            <p className="truncate text-xs text-muted-foreground">{profile?.email}</p>
          </div>
        </div>

        {/* Barre de progression */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-muted-foreground">Complétude du profil</span>
            <span className={progressPercent === 100 ? 'text-emerald-600 dark:text-emerald-400' : 'text-brand'}>
              {progressPercent}%
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className={`h-full rounded-full transition-all duration-500 ease-out ${
                progressPercent === 100 ? 'bg-emerald-500' : 'bg-brand'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Liste des infos manquantes */}
        <div className="space-y-2">
          {missing.length > 0 ? (
            <>
              <span className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 dark:text-amber-400">
                <AlertCircle className="size-3.5" />
                Informations manquantes :
              </span>
              <div className="flex flex-wrap gap-1.5">
                {missing.map((field) => (
                  <span
                    key={field}
                    className="inline-flex items-center rounded-md bg-amber-50 px-2 py-1 text-[10px] font-medium text-amber-700 ring-1 ring-amber-600/10 ring-inset dark:bg-amber-950 dark:text-amber-400 dark:ring-amber-500/30"
                  >
                    {field}
                  </span>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-700 ring-1 ring-emerald-600/10 dark:bg-emerald-950 dark:text-emerald-400 dark:ring-emerald-500/30">
              <CheckCircle2 className="size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
              Profil complet ! Vos recommandations sont optimales.
            </div>
          )}
        </div>

        {/* Bouton d'action */}
        {missing.length > 0 && (
          <Link
            to="/dashboard/profil"
            className="flex h-9 w-full items-center justify-center rounded-lg bg-brand text-xs font-semibold text-brand-foreground transition-colors hover:bg-brand-hover"
          >
            Compléter mon profil
          </Link>
        )}
      </CardContent>
    </Card>
  )
}
