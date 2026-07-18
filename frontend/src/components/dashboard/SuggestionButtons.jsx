import { motion } from 'framer-motion'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, scale: 0.95, y: 5 },
  visible: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.2, ease: 'easeOut' } },
}

export default function SuggestionButtons({ suggestions = [], onSelect }) {
  if (!suggestions || suggestions.length === 0) return null

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-wrap gap-2 py-2"
    >
      {suggestions.map((suggestion, idx) => (
        <motion.button
          key={suggestion + idx}
          variants={itemVariants}
          type="button"
          onClick={() => onSelect?.(suggestion)}
          className="rounded-full border border-border/80 bg-card px-4 py-2 text-xs font-semibold text-foreground shadow-xs transition-all duration-200 hover:border-brand/40 hover:bg-brand-light hover:text-brand hover:scale-102 active:scale-98"
        >
          {suggestion}
        </motion.button>
      ))}
    </motion.div>
  )
}
