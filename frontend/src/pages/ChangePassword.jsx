import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/src/contexts/AuthContext'
import { useProfile } from '@/src/contexts/ProfileContext'
import userService from '@/src/services/user'
import { getApiErrorMessage } from '@/src/utils/errors'
import { getDashboardBasePath } from '@/src/utils/navigation'

/** Page changement de mot de passe — partagée entre utilisateur et administrateur */
export default function ChangePassword() {
  const { role } = useAuth()
  const { profile } = useProfile()
  const navigate = useNavigate()
  const basePath = getDashboardBasePath(role ?? profile?.role)

  const [form, setForm] = useState({
    current_password: '',
    new_password: '',
    confirm_new_password: '',
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
    setError('')
    setSuccess('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (form.new_password !== form.confirm_new_password) {
      setError('Les mots de passe ne correspondent pas.')
      return
    }

    setLoading(true)
    try {
      const data = await userService.changePassword(form)
      setSuccess(data.message)
      setForm({ current_password: '', new_password: '', confirm_new_password: '' })
      setTimeout(() => navigate(`${basePath}/profil`), 2000)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Impossible de changer le mot de passe.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center px-4 py-8 sm:px-6">
      <div className="w-full max-w-md">
        <Link
          to={`${basePath}/profil`}
          className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Retour au profil
        </Link>

        <Card className="border-border/60 shadow-lg">
          <CardHeader className="text-center">
            <CardTitle className="text-xl">Changer le mot de passe</CardTitle>
            <CardDescription>
              Assurez la sécurité de votre compte en utilisant un mot de passe fort
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {error}
                </div>
              )}
              {success && (
                <div className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400">
                  {success}
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="current_password">Mot de passe actuel</Label>
                <Input
                  id="current_password"
                  name="current_password"
                  type="password"
                  value={form.current_password}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new_password">Nouveau mot de passe</Label>
                <Input
                  id="new_password"
                  name="new_password"
                  type="password"
                  value={form.new_password}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm_new_password">Confirmer le mot de passe</Label>
                <Input
                  id="confirm_new_password"
                  name="confirm_new_password"
                  type="password"
                  value={form.confirm_new_password}
                  onChange={handleChange}
                  required
                />
              </div>

              <Button
                type="submit"
                className="w-full bg-brand hover:bg-brand-hover text-brand-foreground"
                disabled={loading}
              >
                {loading ? 'Enregistrement...' : 'Enregistrer la modification'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
