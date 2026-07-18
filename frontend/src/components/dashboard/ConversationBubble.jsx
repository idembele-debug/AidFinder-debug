import { motion } from 'framer-motion'
import { Bot, User } from 'lucide-react'
import { formatLocalDateTime } from '@/src/utils/date'

const bubbleVariants = {
  hidden: { opacity: 0, y: 12, scale: 0.97 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.28, ease: 'easeOut' } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.15 } },
}

/**
 * Curseur clignotant affiché à la fin de la bulle IA pendant le streaming.
 * Utilise une animation CSS pure pour éviter tout re-render inutile.
 */
function StreamingCursor() {
  return (
    <>
      <style>{`
        @keyframes aid-cursor-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        .aid-streaming-cursor {
          display: inline-block;
          width: 2px;
          height: 1em;
          background-color: currentColor;
          margin-left: 2px;
          vertical-align: text-bottom;
          animation: aid-cursor-blink 0.8s ease-in-out infinite;
        }
      `}</style>
      <span className="aid-streaming-cursor" aria-hidden="true" />
    </>
  )
}

/**
 * Bulle de conversation (utilisateur ou assistant).
 *
 * @param {object} props
 * @param {object}  props.msg         - Message à afficher
 * @param {boolean} [props.isStreaming] - Si true, affiche un curseur clignotant (réponse IA en cours)
 */
export default function ConversationBubble({ msg, isStreaming = false }) {
  const isBot = msg.sender === 'assistant'
  const lines = msg.text.split('\n')

  return (
    <motion.div
      layout
      variants={bubbleVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      className={`flex items-end gap-2.5 ${isBot ? 'justify-start' : 'justify-end'}`}
    >
      {/* Avatar Bot */}
      {isBot && (
        <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-brand-light text-brand shadow-xs mb-5">
          <Bot className="size-4" />
        </div>
      )}

      <div className={`flex flex-col gap-1 max-w-[82%] ${isBot ? 'items-start' : 'items-end'}`}>
        {/* Bulle texte */}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-xs ${
            isBot
              ? msg.isError
                ? 'bg-destructive/10 text-destructive border border-destructive/20 rounded-tl-none'
                : 'bg-muted/50 text-foreground border border-border/40 rounded-tl-none'
              : 'bg-brand text-brand-foreground rounded-br-none'
          }`}
        >
          {lines.map((line, i) => (
            <span key={i}>
              {line}
              {i < lines.length - 1 && <br />}
            </span>
          ))}
          {/* Curseur clignotant uniquement sur la bulle IA pendant le streaming */}
          {isBot && isStreaming && <StreamingCursor />}
        </div>

        {/* Timestamp — masqué pendant le streaming */}
        {msg.timestamp && !isStreaming && (
          <span className="text-[10px] text-muted-foreground/60 px-1">
            {formatLocalDateTime(msg.timestamp)}
          </span>
        )}
      </div>

      {/* Avatar Utilisateur */}
      {!isBot && (
        <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-muted text-muted-foreground shadow-xs mb-5">
          <User className="size-4" />
        </div>
      )}
    </motion.div>
  )
}

