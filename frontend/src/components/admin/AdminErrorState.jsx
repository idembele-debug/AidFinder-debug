import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

/**
 * AdminErrorState — composant réutilisable pour les états d'erreur de l'admin.
 */
export default function AdminErrorState({ title = 'Erreur de chargement', description, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex size-16 items-center justify-center rounded-2xl bg-destructive/10">
        <AlertTriangle className="size-8 text-destructive" />
      </div>
      <h3 className="text-base font-bold text-foreground">{title}</h3>
      {description && (
        <p className="mt-2 max-w-sm text-sm text-muted-foreground">{description}</p>
      )}
      {onRetry && (
        <Button onClick={onRetry} className="mt-6 bg-brand hover:bg-brand-hover text-brand-foreground">
          <RefreshCw className="mr-2 size-4" />
          Réessayer
        </Button>
      )}
    </div>
  )
}
