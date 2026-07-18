import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { MessageSquarePlus, Settings, Zap } from 'lucide-react'

export default function QuickActions({ onStartChat }) {
  const actions = [
    {
      label: 'Nouvelle discussion',
      description: 'Lancer le chatbot IA',
      icon: MessageSquarePlus,
      onClick: onStartChat,
      variant: 'default',
      className: 'bg-brand hover:bg-brand-hover text-brand-foreground',
    },
    {
      label: 'Modifier le profil',
      description: 'Gérer vos informations',
      icon: Settings,
      to: '/dashboard/profil',
      variant: 'outline',
      className: 'border-border text-foreground hover:bg-muted/50',
    },
  ]

  return (
    <Card className="border-border/60 bg-card shadow-xs">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
          <Zap className="size-5 text-amber-500" />
          Actions rapides
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3 p-5 lg:grid-cols-1">
        {actions.map((act, index) => {
          const Icon = act.icon
          const content = (
            <div className="flex items-center gap-3 text-left w-full">
              <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted/60 text-muted-foreground group-hover:bg-white/20">
                <Icon className="size-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-bold text-foreground group-hover:text-white">
                  {act.label}
                </p>
                <p className="truncate text-[10px] text-muted-foreground group-hover:text-white/80">
                  {act.description}
                </p>
              </div>
            </div>
          )

          if (act.to) {
            return (
              <Button
                key={index}
                variant={act.variant}
                className={`group h-auto w-full justify-start rounded-xl px-3 py-3 border ${act.className}`}
                asChild
              >
                <Link to={act.to}>{content}</Link>
              </Button>
            )
          }

          return (
            <Button
              key={index}
              variant={act.variant}
              onClick={act.onClick}
              className={`group h-auto w-full justify-start rounded-xl px-3 py-3 border ${act.className}`}
            >
              {content}
            </Button>
          )
        })}
      </CardContent>
    </Card>
  )
}
