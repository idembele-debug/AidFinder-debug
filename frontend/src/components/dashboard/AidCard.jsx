import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ExternalLink, Sparkles, CheckCircle2, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import dashboardService from '@/src/services/dashboardService'

/**
 * Carte de compatibilité interactive avec pliage/dépliage "Pourquoi ?"
 */
function CompatibilityCard({ score, raisons }) {
  const [isOpen, setIsOpen] = useState(false)
  if (score == null) return null

  const pct = Math.min(100, Math.max(0, score))
  
  let badgeColor = 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950/50 ring-red-600/20 dark:ring-red-400/30'
  let barColor = 'bg-red-400 dark:bg-red-500'
  if (pct >= 80) {
    badgeColor = 'text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 ring-emerald-600/20 dark:ring-emerald-400/30'
    barColor = 'bg-emerald-500'
  } else if (pct >= 50) {
    badgeColor = 'text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50 ring-amber-600/20 dark:ring-amber-400/30'
    barColor = 'bg-amber-500'
  }

  return (
    <div className="rounded-xl border border-border/40 bg-muted/20 p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <span className="text-[9px] font-bold uppercase tracking-wider text-muted-foreground">
            Compatibilité
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-extrabold text-foreground">{pct}%</span>
          </div>
        </div>
        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px] font-bold ring-1 ${badgeColor}`}>
          <Sparkles className="size-2.5" />
          Score
        </span>
      </div>

      {/* Progress Bar */}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/65">
        <motion.div
          className={`h-full rounded-full ${barColor}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
        />
      </div>

      {/* Pourquoi ? Toggle */}
      {raisons && raisons.length > 0 && (
        <div className="pt-0.5">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-0.5 text-[10px] font-bold text-brand hover:text-brand-hover transition-colors outline-none"
          >
            Pourquoi ?
            {isOpen ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
          </button>

          <AnimatePresence initial={false}>
            {isOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1, transition: { height: { duration: 0.2 }, opacity: { duration: 0.15 } } }}
                exit={{ height: 0, opacity: 0, transition: { height: { duration: 0.15 }, opacity: { duration: 0.1 } } }}
                className="overflow-hidden"
              >
                <ul className="mt-2 space-y-1 border-t border-border/40 pt-2">
                  {raisons.map((reason, i) => {
                    const isNegative =
                      reason.toLowerCase().includes('non compatible') ||
                      reason.toLowerCase().includes('non renseigné') ||
                      reason.toLowerCase().includes('requis') && !reason.toLowerCase().includes('non requis');
                    return (
                      <li key={i} className="flex items-start gap-1 text-[10px] leading-relaxed text-foreground/80">
                        {isNegative ? (
                          <AlertTriangle className="mt-0.5 size-3 shrink-0 text-amber-500" />
                        ) : (
                          <CheckCircle2 className="mt-0.5 size-3 shrink-0 text-emerald-500" />
                        )}
                        <span>{reason}</span>
                      </li>
                    )
                  })}
                </ul>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}

/**
 * Carte d'aide recommandée modernisée
 */
export default function AidCard({ aid, index = 0, historiqueId = null, onShowDetail = null }) {
  const imageSrc =
    aid.image_url ||
    'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=500&auto=format&fit=crop&q=60'

  const score = aid.compatibilite ?? aid.score_matching ?? null

  const handleConsult = async () => {
    try {
      if (historiqueId) {
        await dashboardService.recordChatConsultation(historiqueId, aid.aide_id)
      } else {
        await dashboardService.recordAidConsultation(aid.aide_id)
      }
    } catch (err) {
      console.error("Erreur enregistrement consultation:", err)
    } finally {
      const externalUrl = aid.url_officielle ?? aid.lien_officiel
      if (externalUrl) {
        window.open(externalUrl, '_blank', 'noopener,noreferrer')
      } else if (onShowDetail) {
        onShowDetail(aid)
      }
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut', delay: index * 0.08 }}
    >
      <Card className="group flex flex-col overflow-hidden border-border/50 bg-card shadow-xs transition-all duration-300 hover:shadow-md hover:-translate-y-1">
        {/* Image Section */}
        <div className="relative h-36 w-full overflow-hidden bg-muted">
          <img
            src={imageSrc}
            alt={aid.titre}
            className="size-full object-cover transition-transform duration-500 group-hover:scale-103"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
          {aid.type_aide && (
            <span className="absolute top-2 left-2 rounded-full bg-background/90 px-2.5 py-1 text-[10px] font-semibold text-brand shadow-xs backdrop-blur-xs">
              {aid.type_aide}
            </span>
          )}
        </div>

        {/* Content Section */}
        <CardContent className="flex flex-1 flex-col gap-3 p-4">
          <div className="space-y-0.5">
            <h4 className="line-clamp-2 text-sm font-bold leading-tight text-foreground transition-colors group-hover:text-brand">
              {aid.titre}
            </h4>
            {aid.region_cible && (
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                {aid.region_cible}
              </p>
            )}
          </div>

          <p className="line-clamp-2 text-xs leading-relaxed text-muted-foreground">
            {aid.description || 'Aucune description disponible.'}
          </p>

          {/* Carte de Compatibilité */}
          <CompatibilityCard score={score} raisons={aid.raisons} />

          <div className="mt-auto pt-1">
            <Button
              onClick={handleConsult}
              className="w-full bg-brand hover:bg-brand-hover text-brand-foreground rounded-lg text-xs font-semibold"
              id={`consult-aid-${aid.aide_id}`}
            >
              Consulter
              <ExternalLink className="ml-1.5 size-3.5" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
