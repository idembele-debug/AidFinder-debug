import { useRef, useEffect } from 'react'
import { Send, PlusCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'

/**
 * Zone de saisie du chat — Textarea auto-resize, Enter pour envoyer, Shift+Enter pour saut de ligne.
 * @param {object} props
 * @param {string} props.value - Valeur contrôlée depuis le parent
 * @param {function} props.onChange - Setter de la valeur
 * @param {function} props.onSend - Callback appelé avec le texte à envoyer
 * @param {boolean} props.disabled - Désactive le champ et le bouton pendant l'envoi
 */
export default function ChatInput({ onSend, value = '', onChange, disabled = false }) {
  const textareaRef = useRef(null)
  const navigate = useNavigate()

  // Auto-resize du textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [value])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleSubmit = () => {
    if (!value.trim() || disabled) return
    onSend?.(value.trim())
    onChange?.('')
  }

  const handleNewChat = () => {
    navigate('/dashboard/discussion')
  }

  return (
    <div className="mx-auto w-full max-w-3xl">
      <div className="flex items-end gap-2 rounded-2xl border border-border/80 bg-background px-4 py-3 shadow-sm transition-shadow focus-within:border-brand/60 focus-within:shadow-md">
        {/* Bouton Nouveau Chat */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={handleNewChat}
          className="mb-0.5 shrink-0 size-8 text-muted-foreground hover:text-brand hover:bg-brand-light"
          aria-label="Nouvelle discussion"
          title="Nouvelle discussion"
        >
          <PlusCircle className="size-5" />
        </Button>

        {/* Textarea auto-resize */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Décrivez votre situation... (Shift+Entrée pour un saut de ligne)"
          disabled={disabled}
          className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground/70 outline-none min-h-[28px] max-h-40 leading-relaxed disabled:opacity-60"
          aria-label="Saisir votre message"
          id="chat-input"
        />

        {/* Bouton Envoyer */}
        <Button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="mb-0.5 shrink-0 size-8 rounded-xl bg-brand text-brand-foreground shadow-none hover:bg-brand-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          size="icon"
          aria-label="Envoyer le message"
          id="chat-send-btn"
        >
          <Send className="size-4" />
        </Button>
      </div>

      <p className="mt-2 text-center text-[10px] text-muted-foreground/60">
        AidFinder IA peut faire des erreurs. Vérifiez les informations importantes.
      </p>
    </div>
  )
}
