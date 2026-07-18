import { motion } from 'framer-motion'
import { X, ExternalLink, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

const overlayVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.25 } },
}

const modalVariants = {
  hidden: { opacity: 0, scale: 0.95, y: 16 },
  visible: { opacity: 1, scale: 1, y: 0, transition: { type: 'spring', damping: 25, stiffness: 350 } },
}

export default function AidDetailModal({ aid, onClose, onConsult }) {
  if (!aid) return null

  const imageSrc =
    aid.image_url ||
    'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=500&auto=format&fit=crop&q=60'

  const score = aid.compatibilite ?? aid.score_matching ?? null

  const getScoreColor = (val) => {
    if (val >= 80) return 'text-emerald-500 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 border-emerald-200 dark:border-emerald-800'
    if (val >= 50) return 'text-amber-500 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50 border-amber-200 dark:border-amber-800'
    return 'text-red-500 dark:text-red-400 bg-red-50 dark:bg-red-950/50 border-red-200 dark:border-red-800'
  }

  return (
    <motion.div
      variants={overlayVariants}
      initial="hidden"
      animate="visible"
      exit="hidden"
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs"
    >
      <motion.div
        variants={modalVariants}
        onClick={(e) => e.stopPropagation()}
        className="relative flex w-full max-w-2xl flex-col overflow-hidden rounded-3xl border border-border/80 bg-card shadow-2xl"
      >
        {/* Header Image */}
        <div className="relative h-52 w-full overflow-hidden bg-muted">
          <img src={imageSrc} alt={aid.titre} className="size-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
          
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 flex size-9 items-center justify-center rounded-full bg-black/45 text-white/90 backdrop-blur-md transition-all hover:bg-black/60 hover:scale-105"
            aria-label="Fermer"
            id="close-aid-modal"
          >
            <X className="size-5" />
          </button>

          {/* Badge & Titre sur l'image */}
          <div className="absolute bottom-4 left-6 right-6 space-y-2">
            {aid.type_aide && (
              <span className="inline-block rounded-full bg-background/95 px-3 py-1 text-[10px] font-bold text-brand shadow-sm uppercase tracking-wider">
                {aid.type_aide}
              </span>
            )}
            <h3 className="text-xl font-extrabold text-white leading-tight drop-shadow-sm">
              {aid.titre}
            </h3>
          </div>
        </div>

        {/* Content */}
        <div className="max-h-[50vh] overflow-y-auto p-6 md:p-8 space-y-6">
          
          {/* Métadonnées rapides */}
          <div className="flex flex-wrap items-center gap-4 text-xs font-semibold">
            {aid.region_cible && (
              <span className="rounded-lg bg-muted px-2.5 py-1.5 text-muted-foreground uppercase tracking-wider border border-border/40">
                Région : {aid.region_cible}
              </span>
            )}
            {aid.categorie && (
              <span className="rounded-lg bg-muted px-2.5 py-1.5 text-muted-foreground border border-border/40">
                Catégorie : {aid.categorie}
              </span>
            )}
            {score !== null && (
              <span className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 border ${getScoreColor(score)}`}>
                <Sparkles className="size-3.5" />
                Score : {score}%
              </span>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <h4 className="text-sm font-bold text-foreground uppercase tracking-wide">
              Description de l'aide
            </h4>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {aid.description || 'Aucune description disponible.'}
            </p>
          </div>

          {/* Analyse de compatibilité */}
          {aid.raisons && aid.raisons.length > 0 && (
            <div className="space-y-3 rounded-2xl bg-muted/30 p-5 border border-border/30">
              <h4 className="flex items-center gap-2 text-sm font-bold text-foreground">
                <Sparkles className="size-4 text-brand" />
                Analyse de compatibilité
              </h4>
              <ul className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                {aid.raisons.map((reason, i) => {
                  const isNegative =
                    reason.toLowerCase().includes('non compatible') ||
                    reason.toLowerCase().includes('non renseigné') ||
                    reason.toLowerCase().includes('requis') && !reason.toLowerCase().includes('non requis');
                  return (
                    <li key={i} className="flex items-start gap-2 text-xs text-foreground/80 leading-normal">
                      {isNegative ? (
                        <AlertCircle className="mt-0.5 size-4 shrink-0 text-amber-500" />
                      ) : (
                        <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" />
                      )}
                      <span>{reason}</span>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 border-t border-border/60 bg-muted/20 px-6 py-4 md:px-8">
          <Button
            variant="outline"
            onClick={onClose}
            className="rounded-xl text-xs font-semibold border-border/70 hover:bg-muted"
            id="close-modal-btn"
          >
            Fermer
          </Button>
          {onConsult && (
            <Button
              onClick={onConsult}
              className="bg-brand hover:bg-brand-hover text-brand-foreground rounded-xl text-xs font-semibold"
              id="consult-modal-btn"
            >
              Consulter le site officiel
              <ExternalLink className="ml-1.5 size-3.5" />
            </Button>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}
