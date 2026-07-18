import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { FileText, MessageSquare, Search, Sparkles } from 'lucide-react'

function AnimatedCounter({ value }) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    const end = parseInt(value, 10) || 0
    if (end === 0) return

    let start = 0
    // Calcul de la vitesse pour que l'animation dure environ 1 seconde
    const step = Math.ceil(end / 30) || 1
    const timer = setInterval(() => {
      start += step
      if (start >= end) {
        clearInterval(timer)
        setCount(end)
      } else {
        setCount(start)
      }
    }, 30)

    return () => clearInterval(timer)
  }, [value])

  return <span>{count}</span>
}

export default function StatsCards({
  recherches = 0,
  conversations = 0,
  recommandations = 0,
  pdfExportes = 0,
}) {
  const cards = [
    {
      title: 'Recherches effectuées',
      value: recherches,
      icon: Search,
      color: 'text-blue-600 bg-blue-50 border-blue-100 dark:text-blue-400 dark:bg-blue-950/30 dark:border-blue-800',
    },
    {
      title: 'Conversations',
      value: conversations,
      icon: MessageSquare,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100 dark:text-emerald-400 dark:bg-emerald-950/30 dark:border-emerald-800',
    },
    {
      title: 'Aides recommandées',
      value: recommandations,
      icon: Sparkles,
      color: 'text-amber-600 bg-amber-50 border-amber-100 dark:text-amber-400 dark:bg-amber-950/30 dark:border-amber-800',
    },
    {
      title: 'PDF exportés',
      value: pdfExportes,
      icon: FileText,
      color: 'text-purple-600 bg-purple-50 border-purple-100 dark:text-purple-400 dark:bg-purple-950/30 dark:border-purple-800',
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon
        return (
          <Card key={card.title} className="border-border/60 bg-card shadow-xs transition-all duration-300 hover:shadow-md hover:translate-y-[-2px]">
            <CardContent className="flex items-center gap-4 p-5">
              <div className={`flex size-11 items-center justify-center rounded-xl border ${card.color} shrink-0`}>
                <Icon className="size-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-muted-foreground">
                  {card.title}
                </p>
                <h3 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
                  <AnimatedCounter value={card.value} />
                </h3>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
