import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

/** Carte d'aide en bas de la sidebar — conforme à la maquette */
export default function HelpCard() {
  return (
    <Card className="border-0 bg-card shadow-md">
      <CardHeader className="px-4 pt-4 pb-0">
        <CardTitle className="text-sm font-semibold text-foreground">
          Besoin d&apos;aide ?
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <p className="text-xs leading-relaxed text-muted-foreground">
          Notre chatbot est là pour vous aider.
        </p>
      </CardContent>
    </Card>
  )
}
