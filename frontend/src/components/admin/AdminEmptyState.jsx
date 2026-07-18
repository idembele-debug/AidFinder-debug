import { cn } from '@/lib/utils'

/**
 * AdminEmptyState — composant réutilisable pour les états vides de l'admin.
 */
export default function AdminEmptyState({ icon: Icon, title, description, action, className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      {Icon && (
        <div className="mb-4 flex size-16 items-center justify-center rounded-2xl bg-brand-light">
          <Icon className="size-8 text-brand" />
        </div>
      )}
      <h3 className="text-base font-bold text-foreground">{title}</h3>
      {description && (
        <p className="mt-2 max-w-sm text-sm text-muted-foreground">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
