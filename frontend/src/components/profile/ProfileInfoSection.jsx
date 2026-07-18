import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getApiErrorMessage } from '@/src/utils/errors'
import {
  REGIONS,
  NIVEAUX_ETUDE,
  STATUTS_SOCIO_PRO,
} from '@/src/constants/profileOptions'

const selectClass =
  'flex h-9 w-full rounded-lg border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

function InfoRow({ label, value }) {
  return (
    <div className="flex flex-col gap-1 border-b border-border/60 py-3 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value || '—'}</span>
    </div>
  )
}

/** Section informations personnelles — affichage et édition */
export default function ProfileInfoSection({ profile, onSave }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const startEditing = () => {
    setForm({
      nom: profile?.nom || '',
      date_naissance: profile?.date_naissance || '',
      region: profile?.region || '',
      niveau_etude: profile?.niveau_etude || '',
      statut_socio_pro: profile?.statut_socio_pro || '',
      situation_handicap: profile?.situation_handicap || false,
    })
    setEditing(true)
    setError('')
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { nom: form.nom }
      if (form.date_naissance) payload.date_naissance = form.date_naissance
      if (form.region) payload.region = form.region
      if (form.niveau_etude) payload.niveau_etude = form.niveau_etude
      if (form.statut_socio_pro) payload.statut_socio_pro = form.statut_socio_pro
      payload.situation_handicap = form.situation_handicap

      await onSave(payload)
      setEditing(false)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Impossible de mettre à jour le profil.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="border-border/60 shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base">Informations personnelles</CardTitle>
        {!editing && (
          <button
            type="button"
            onClick={startEditing}
            className="text-sm font-medium text-brand hover:underline"
          >
            Modifier
          </button>
        )}
      </CardHeader>
      <CardContent>
        {editing ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="nom">Nom & Prénom</Label>
              <Input id="nom" name="nom" value={form.nom} onChange={handleChange} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="date_naissance">Date de naissance</Label>
              <Input
                id="date_naissance"
                name="date_naissance"
                type="date"
                value={form.date_naissance}
                onChange={handleChange}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="region">Région</Label>
              <select
                id="region"
                name="region"
                value={form.region}
                onChange={handleChange}
                className={selectClass}
              >
                <option value="">Sélectionnez votre région</option>
                {REGIONS.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="niveau_etude">Niveau d&apos;étude</Label>
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
              <Label htmlFor="statut_socio_pro">Statut socioprofessionnel</Label>
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
              Situation de handicap
            </label>
            <div className="flex gap-2">
              <Button type="submit" className="bg-brand hover:bg-brand-hover text-brand-foreground" disabled={saving}>
                {saving ? 'Enregistrement...' : 'Enregistrer'}
              </Button>
              <Button type="button" variant="outline" onClick={() => setEditing(false)}>
                Annuler
              </Button>
            </div>
          </form>
        ) : (
          <div>
            <InfoRow label="Nom & Prénom" value={profile?.nom} />
            <InfoRow label="Email" value={profile?.email} />
            <InfoRow label="Rôle" value={profile?.role} />
            <InfoRow label="Date de naissance" value={profile?.date_naissance} />
            <InfoRow label="Région" value={profile?.region} />
            <InfoRow label="Niveau d'étude" value={profile?.niveau_etude} />
            <InfoRow label="Statut socioprofessionnel" value={profile?.statut_socio_pro} />
            <InfoRow
              label="Situation de handicap"
              value={profile?.situation_handicap ? 'Oui' : 'Non'}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
