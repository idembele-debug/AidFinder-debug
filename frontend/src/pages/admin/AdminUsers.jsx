import { useState, useEffect } from 'react'
import { Users, Eye, Search, RefreshCw, X, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import useAdminUsers from '@/src/hooks/useAdminUsers'
import { AdminTableSkeleton } from '@/src/components/admin/AdminSkeletons'
import AdminEmptyState from '@/src/components/admin/AdminEmptyState'
import AdminErrorState from '@/src/components/admin/AdminErrorState'
import { getApiBaseUrl } from '@/src/config/env'
import { formatLocalDate } from '@/src/utils/date'
import { useToast } from '@/src/contexts/ToastContext'
import adminService from '@/src/services/admin'

/* ─────────────────────────────────────────────────────────────── */
/*  Sub-components                                                  */
/* ─────────────────────────────────────────────────────────────── */

function UserAvatar({ user }) {
  const initials = user.nom
    ? user.nom.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : '?'

  if (user.photo_profil) {
    return (
      <img
        src={`${getApiBaseUrl()}${user.photo_profil}`}
        alt={user.nom}
        className="size-10 rounded-full object-cover border border-border"
      />
    )
  }
  return (
    <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-light text-sm font-bold text-brand border border-brand-border">
      {initials}
    </div>
  )
}

function StatusBadge({ status }) {
  const isSuspended = status === 'suspendu'
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold ${
        isSuspended
          ? 'bg-red-50 text-red-700 ring-1 ring-red-600/20 dark:bg-red-950 dark:text-red-400 dark:ring-red-500/30'
          : 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20 dark:bg-emerald-950 dark:text-emerald-400 dark:ring-emerald-500/30'
      }`}
    >
      <span className={`size-1.5 rounded-full ${isSuspended ? 'bg-red-500' : 'bg-emerald-500'}`} />
      {isSuspended ? 'Suspendu' : 'Actif'}
    </span>
  )
}

/* ─────────────────────────────────────────────────────────────── */
/*  Modal Voir                                                      */
/* ─────────────────────────────────────────────────────────────── */

function UserDetailModal({ user, onClose }) {
  const [warnings, setWarnings] = useState([])
  const [loadingWarnings, setLoadingWarnings] = useState(true)

  useEffect(() => {
    if (!user) return
    let active = true
    const fetchWarnings = async () => {
      try {
        const data = await adminService.getUserWarnings(user.user_id)
        if (active) setWarnings(data)
      } catch (err) {
        console.error("Erreur lors de la récupération des avertissements", err)
      } finally {
        if (active) setLoadingWarnings(false)
      }
    }
    fetchWarnings()
    return () => {
      active = false
    }
  }, [user])

  if (!user) return null

  const isSuspended = user.statut_compte === 'suspendu'
  const dateSuspension = isSuspended && user.date_fin_suspension
    ? new Date(new Date(user.date_fin_suspension).getTime() - 15 * 24 * 60 * 60 * 1000).toISOString()
    : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-2xl bg-card p-6 shadow-2xl space-y-4 overflow-y-auto max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-foreground">Détails de l'utilisateur</h2>
          <button onClick={onClose} className="rounded-lg p-1 hover:bg-muted/50 text-muted-foreground">
            <X className="size-4" />
          </button>
        </div>

        <div className="flex items-center gap-4">
          <UserAvatar user={user} />
          <div>
            <p className="font-bold text-foreground">{user.nom}</p>
            <p className="text-sm text-muted-foreground">{user.email}</p>
          </div>
          <StatusBadge status={user.statut_compte} />
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          {[
            ['Rôle', user.role],
            ['Région', user.region || '—'],
            ['Niveau étude', user.niveau_etude || '—'],
            ['Statut pro', user.statut_socio_pro || '—'],
            ['Inscription', formatLocalDate(user.date_creation)],
            ['Dernière connexion', formatLocalDate(user.date_derniere_connexion)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg bg-muted/30 p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
              <p className="mt-0.5 font-semibold text-foreground">{value}</p>
            </div>
          ))}
        </div>

        {/* Section Modération */}
        <div className="border-t border-border/60 pt-4 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Historique de modération</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg bg-muted/30 p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Nombre d'avertissements</p>
              <p className="mt-0.5 font-semibold text-foreground">{user.nombre_avertissements}</p>
            </div>
            <div className="rounded-lg bg-muted/30 p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Dernier avertissement</p>
              <p className="mt-0.5 font-semibold text-foreground">
                {loadingWarnings ? (
                  <span className="text-xs text-muted-foreground">Chargement...</span>
                ) : (
                  warnings[0] ? formatLocalDate(warnings[0].date_creation) : 'Aucun'
                )}
              </p>
            </div>
            {isSuspended && (
              <>
                <div className="rounded-lg bg-destructive/10 p-3 border border-destructive/20">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-destructive">Date de suspension</p>
                  <p className="mt-0.5 font-semibold text-destructive">
                    {dateSuspension ? formatLocalDate(dateSuspension) : '—'}
                  </p>
                </div>
                <div className="rounded-lg bg-destructive/10 p-3 border border-destructive/20">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-destructive">Réactivation prévue</p>
                  <p className="mt-0.5 font-semibold text-destructive">
                    {user.date_fin_suspension ? formatLocalDate(user.date_fin_suspension) : '—'}
                  </p>
                </div>
              </>
            )}
          </div>
        </div>

        <Button onClick={onClose} className="w-full" variant="outline">Fermer</Button>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────── */
/*  Modal Avertir                                                   */
/* ─────────────────────────────────────────────────────────────── */

function WarningModal({ user, onClose, onConfirm }) {
  const [motif, setMotif] = useState('')
  const [discussionId, setDiscussionId] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!user) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!motif.trim() || !discussionId) return
    setSubmitting(true)
    try {
      await onConfirm(user.user_id, {
        motif: motif.trim(),
        discussion_id: parseInt(discussionId, 10),
      })
      onClose()
    } catch (err) {
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  const inputClass =
    'w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all'
  const labelClass = 'block text-xs font-semibold text-muted-foreground mb-1'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-2xl bg-card p-6 shadow-2xl space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-foreground">Avertir l'utilisateur</h2>
          <button onClick={onClose} className="rounded-lg p-1 hover:bg-muted/50 text-muted-foreground">
            <X className="size-4" />
          </button>
        </div>

        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800 dark:bg-amber-950 dark:border-amber-500/30 dark:text-amber-400">
          Avertir cet utilisateur entraînera l'envoi d'un e-mail d'avertissement. Au bout de 2 avertissements, le compte sera automatiquement suspendu pour 15 jours.
        </div>

        <div className="space-y-1 text-sm">
          <p><span className="font-semibold text-muted-foreground">Utilisateur :</span> {user.nom}</p>
          <p><span className="font-semibold text-muted-foreground">Email :</span> {user.email}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className={labelClass}>ID de la discussion ayant provoqué l'avertissement *</label>
            <input
              type="number"
              className={inputClass}
              value={discussionId}
              onChange={(e) => setDiscussionId(e.target.value)}
              placeholder="Ex : 12"
              required
            />
          </div>

          <div>
            <label className={labelClass}>Motif / Raison de l'avertissement *</label>
            <textarea
              className={`${inputClass} resize-none`}
              rows={3}
              value={motif}
              onChange={(e) => setMotif(e.target.value)}
              placeholder="Renseignez le motif de l'avertissement..."
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Annuler
            </Button>
            <Button
              type="submit"
              disabled={submitting || !motif.trim() || !discussionId}
              className="gap-2 bg-amber-600 hover:bg-amber-700 text-white dark:bg-amber-700 dark:hover:bg-amber-600"
            >
              {submitting && <RefreshCw className="size-4 animate-spin" />}
              Confirmer
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────── */
/*  Page principale                                                 */
/* ─────────────────────────────────────────────────────────────── */

export default function AdminUsers() {
  const { users, loading, error, refresh } = useAdminUsers()
  const { showToast } = useToast()
  const [search, setSearch] = useState('')
  const [viewUser, setViewUser] = useState(null)
  const [warnUser, setWarnUser] = useState(null)

  const filtered = users.filter(
    (u) =>
      u.nom?.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase())
  )

  const handleConfirmWarning = async (userId, payload) => {
    try {
      await adminService.createWarning(userId, payload)
      showToast('Avertissement envoyé avec succès.', 'success')
      refresh()
    } catch (err) {
      const errMsg = err.response?.data?.detail || "Impossible d'envoyer l'avertissement."
      showToast(errMsg, 'error')
      throw err
    }
  }

  return (
    <div className="flex-1 bg-muted/20 px-4 py-6 sm:px-6 lg:px-8 lg:py-8 space-y-6">
      {/* Modals */}
      {viewUser && <UserDetailModal user={viewUser} onClose={() => setViewUser(null)} />}
      {warnUser && (
        <WarningModal
          user={warnUser}
          onClose={() => setWarnUser(null)}
          onConfirm={handleConfirmWarning}
        />
      )}

      {/* En-tête */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-foreground sm:text-2xl">
            <Users className="size-6 text-brand" />
            Gestion des utilisateurs
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {users.length} utilisateur{users.length !== 1 ? 's' : ''} au total
          </p>
        </div>
        <Button onClick={refresh} variant="outline" size="sm" className="gap-2">
          <RefreshCw className="size-4" /> Actualiser
        </Button>
      </div>

      {/* Barre de recherche */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Rechercher par nom ou email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-border bg-background py-2.5 pl-10 pr-4 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 transition-all"
        />
      </div>

      {/* Contenu */}
      {loading ? (
        <AdminTableSkeleton cols={5} rows={8} />
      ) : error ? (
        <AdminErrorState description="Impossible de charger les utilisateurs." onRetry={refresh} />
      ) : filtered.length === 0 ? (
        <AdminEmptyState
          icon={Users}
          title="Aucun utilisateur trouvé"
          description={search ? 'Aucun résultat pour cette recherche.' : 'Aucun utilisateur enregistré.'}
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-border/60 bg-card shadow-sm">
          {/* Vue desktop */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/60 bg-muted/30">
                  <th className="px-6 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Utilisateur</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Email</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Statut</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Avertissements</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Inscription</th>
                  <th className="px-6 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filtered.map((user) => (
                  <tr key={user.user_id} className="hover:bg-muted/20 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <UserAvatar user={user} />
                        <span className="font-semibold text-foreground">{user.nom}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground">{user.email}</td>
                    <td className="px-6 py-4">
                      <StatusBadge status={user.statut_compte} />
                    </td>
                    <td className="px-6 py-4 text-muted-foreground text-sm">{user.nombre_avertissements}</td>
                    <td className="px-6 py-4 text-muted-foreground text-xs">{formatLocalDate(user.date_creation)}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost" size="icon"
                          onClick={() => setViewUser(user)}
                          className="size-8 text-muted-foreground hover:text-brand hover:bg-brand-light"
                          title="Voir"
                        >
                          <Eye className="size-4" />
                        </Button>
                        <Button
                          variant="ghost" size="icon"
                          onClick={() => setWarnUser(user)}
                          className="size-8 text-muted-foreground hover:text-amber-600 hover:bg-amber-50 dark:hover:text-amber-400 dark:hover:bg-amber-950/50"
                          title="Avertir"
                        >
                          <AlertTriangle className="size-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Vue mobile — cartes */}
          <div className="md:hidden divide-y divide-border/60">
            {filtered.map((user) => (
              <div key={user.user_id} className="p-4 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-3 min-w-0">
                    <UserAvatar user={user} />
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-foreground">{user.nom}</p>
                      <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <StatusBadge status={user.statut_compte} />
                    <span className="text-[10px] text-muted-foreground">
                      {user.nombre_avertissements} {user.nombre_avertissements > 1 ? 'avertissements' : 'avertissement'}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-muted-foreground">Inscrit le {formatLocalDate(user.date_creation)}</p>

                <div className="flex flex-wrap items-center gap-1">
                  <Button variant="ghost" size="icon" onClick={() => setViewUser(user)} className="size-8 hover:text-brand">
                    <Eye className="size-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setWarnUser(user)} className="size-8 hover:text-amber-600 dark:hover:text-amber-400">
                    <AlertTriangle className="size-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
