import { motion } from 'framer-motion'
import { Bot } from 'lucide-react'

export default function TypingIndicator() {
  const dotVariants = {
    initial: { y: 0 },
    animate: {
      y: [0, -6, 0],
      transition: {
        duration: 0.8,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  }

  const containerVariants = {
    animate: {
      transition: {
        staggerChildren: 0.15,
      },
    },
  }

  return (
    <div className="flex items-start gap-3">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-brand-light text-brand shadow-xs">
        <Bot className="size-4" />
      </div>
      <div className="flex items-center gap-2 rounded-2xl rounded-tl-none border border-border/40 bg-muted/40 px-5 py-3.5">
        <span className="text-xs font-medium text-muted-foreground/90">
          AidFinder IA est en train d'écrire
        </span>
        <motion.div
          className="flex items-center gap-1"
          variants={containerVariants}
          initial="initial"
          animate="animate"
        >
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              variants={dotVariants}
              className="size-1.5 rounded-full bg-brand"
            />
          ))}
        </motion.div>
      </div>
    </div>
  )
}
