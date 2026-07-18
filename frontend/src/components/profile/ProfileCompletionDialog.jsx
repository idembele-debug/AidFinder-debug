import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useProfile } from '@/src/contexts/ProfileContext'
import { getApiErrorMessage } from '@/src/utils/errors'
import {
  REGIONS,
  NIVEAUX_ETUDE,
  STATUTS_SOCIO_PRO,
} from '@/src/constants/profileOptions'

const selectClass =
  'flex h-9 w-full rounded-lg border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

/**
 * Fenêtre obligatoire de complétion du profil.
 * Bloque l'accès au Dashboard tant que date de naissance et région ne sont pas renseignées.
 */
export default function ProfileCompletionDialog() {
  const { profile, loading, isProfileComplete, updateProfile } = useProfile()
  const [form, setForm] = useState({
    date_naissance: '',
    region: '',
    niveau_etude: '',
    statut_socio_pro: '',
    situation_handicap: false,
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const open = !loading && profile && !isProfileComplete

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!form.date_naissance || !form.region) {
      setError('La date de naissance et la région sont obligatoires.')
      return
    }

    setSubmitting(true)
    try {
      const payload = {
        date_naissance: form.date_naissance,
        region: form.region,
      }
      if (form.niveau_etude) payload.niveau_etude = form.niveau_etude
      if (form.statut_socio_pro) payload.statut_socio_pro = form.statut_socio_pro
      payload.situation_handicap = form.situation_handicap

      await updateProfile(payload)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Impossible de mettre à jour le profil.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open}>
      <DialogContent
        showClose={false}
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
        className="max-h-[90vh] overflow-y-auto sm:max-w-md"
      >
        <DialogHeader>
          <DialogTitle className="text-xl">Bienvenue sur AidFinder</DialogTitle>
          <DialogDescription className="space-y-3 pt-2 text-left leading-relaxed">
            <span className="block">
              Afin de vous proposer les aides financières les plus adaptées à votre
              situation, nous avons besoin de quelques informations complémentaires.
            </span>
            <span className="block">
              Seules votre <strong>date de naissance</strong> et votre{' '}
              <strong>région</strong> sont obligatoires.
            </span>
            <span className="block">
              Les autres informations sont facultatives et pourront être complétées
              ultérieurement depuis votre profil.
            </span>
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="date_naissance">
              Date de naissance <span className="text-destructive">*</span>
            </Label>
            <Input
              id="date_naissance"
              name="date_naissance"
              type="date"
              value={form.date_naissance}
              onChange={handleChange}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="region">
              Région <span className="text-destructive">*</span>
            </Label>
            <select
              id="region"
              name="region"
              value={form.region}
              onChange={handleChange}
              required
              className={selectClass}
            >
              <option value="">Sélectionnez votre région</option>
              {REGIONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="niveau_etude">Niveau d&apos;étude (facultatif)</Label>
            <select
              id="niveau_etude"
              name="niveau_etude"
              value={form.niveau_etude}
              onChange={handleChange}
              className={selectClass}
            >
              <option value="">Non renseigné</option>
              {NIVEAUX_ETUDE.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="statut_socio_pro">Statut socioprofessionnel (facultatif)</Label>
            <select
              id="statut_socio_pro"
              name="statut_socio_pro"
              value={form.statut_socio_pro}
              onChange={handleChange}
              className={selectClass}
            >
              <option value="">Non renseigné</option>
              {STATUTS_SOCIO_PRO.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              name="situation_handicap"
              checked={form.situation_handicap}
              onChange={handleChange}
              className="size-4 rounded border-input"
            />
            Situation de handicap (facultatif)
          </label>

          <Button
            type="submit"
            className="w-full bg-brand hover:bg-brand-hover text-brand-foreground"
            disabled={submitting}
          >
            {submitting ? 'Enregistrement...' : 'Continuer'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
