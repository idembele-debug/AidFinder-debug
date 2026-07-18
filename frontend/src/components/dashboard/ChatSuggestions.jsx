import { motion } from 'framer-motion'
import { Search, Building2, GraduationCap, Briefcase } from 'lucide-react'

const SUGGESTIONS = [
  {
    icon: Search,
    label: 'Trouver une aide',
    description: 'Explorez toutes les aides disponibles',
  },
  {
    icon: Building2,
    label: 'Créer mon entreprise',
    description: 'Aides à la création et entrepreneuriat',
  },
  {
    icon: GraduationCap,
    label: 'Je suis étudiant',
    description: 'Bourses, logement et aides étudiantes',
  },
  {
    icon: Briefcase,
    label: 'Je cherche un emploi',
    description: 'Accompagnement et aides à l\'emploi',
  },
]

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' } },
}

/** Boutons de suggestions rapides pour le chatbot — affichés uniquement sans conversation */
export default function ChatSuggestions({ onSelect }) {
  return (
    <motion.div
      className="grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {SUGGESTIONS.map(({ icon: Icon, label, description }) => (
        <motion.button
          key={label}
          variants={itemVariants}
          onClick={() => onSelect?.(label)}
          className="group flex items-start gap-3 rounded-2xl border border-border/70 bg-card px-4 py-4 text-left shadow-xs transition-all duration-200 hover:border-brand/40 hover:bg-brand-light hover:shadow-sm"
          type="button"
        >
          <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-brand-light text-brand transition-colors group-hover:bg-brand-lighter">
            <Icon className="size-4" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-foreground">{label}</p>
            <p className="mt-0.5 text-xs text-muted-foreground leading-snug">{description}</p>
          </div>
        </motion.button>
      ))}
    </motion.div>
  )
}
