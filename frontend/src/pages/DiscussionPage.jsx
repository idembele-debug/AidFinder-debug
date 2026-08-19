import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Bot,
  AlertTriangle,
  RefreshCw,
  Plus,
  Sparkles,
} from 'lucide-react'
import dashboardService from '@/src/services/dashboardService'
import useStreamingChat from '@/src/hooks/useStreamingChat'
import ChatSuggestions from '@/src/components/dashboard/ChatSuggestions'
import ChatInput from '@/src/components/dashboard/ChatInput'
import AidCard from '@/src/components/dashboard/AidCard'
import ConversationBubble from '@/src/components/dashboard/ConversationBubble'
import TypingIndicator from '@/src/components/dashboard/TypingIndicator'
import SuggestionButtons from '@/src/components/dashboard/SuggestionButtons'
import AidDetailModal from '@/src/components/dashboard/AidDetailModal'
import { ChatMessageSkeleton } from '@/src/components/dashboard/SkeletonLoader'
import { Button } from '@/components/ui/button'

/* ─────────────────────────────────────────
   Variants Framer Motion
   ───────────────────────────────────────── */
const messageVariants = {
  hidden: { opacity: 0, y: 12, scale: 0.97 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.28, ease: 'easeOut' } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.15 } },
}

const sectionVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
}

/* ─────────────────────────────────────────
   Empty State (aucune conversation)
   ───────────────────────────────────────── */
function EmptyChatState({ onSelect }) {
  return (
    <motion.div
      variants={sectionVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-col items-center justify-center py-8 text-center"
    >
      <div className="mb-5 flex size-16 items-center justify-center rounded-2xl bg-brand-light text-brand shadow-xs animate-pulse">
        <Sparkles className="size-7" />
      </div>

      <div className="mb-6 max-w-lg">
        <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
          Comment pouvons-nous vous aider ?
        </h1>
        <p className="mt-3 text-sm text-muted-foreground sm:text-base leading-relaxed">
          Discutez avec notre assistant pour découvrir les aides financières qui vous correspondent.
        </p>
      </div>

      <ChatSuggestions onSelect={onSelect} />
    </motion.div>
  )
}

/* ─────────────────────────────────────────
   Section cartes d'aides recommandées
   ───────────────────────────────────────── */
function AidsRecommendedSection({ aids, historiqueId, onShowDetail }) {
  if (!aids || aids.length === 0) return null

  return (
    <motion.div
      variants={sectionVariants}
      initial="hidden"
      animate="visible"
      className="mt-8 border-t border-border/50 pt-6"
    >
      <div className="mb-4 flex items-center gap-2">
        <div className="flex size-7 items-center justify-center rounded-lg bg-brand-light text-brand">
          <Sparkles className="size-3.5" />
        </div>
        <h2 className="text-sm font-bold text-foreground">Aides recommandées pour vous</h2>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {aids.map((aid, i) => (
          <AidCard
            key={aid.aide_id}
            aid={aid}
            index={i}
            historiqueId={historiqueId}
            onShowDetail={onShowDetail}
          />
        ))}
      </div>
    </motion.div>
  )
}

/* ─────────────────────────────────────────
   ID unique pour la bulle streaming
   ───────────────────────────────────────── */
const STREAMING_BUBBLE_ID = '__streaming__'

/* ─────────────────────────────────────────
   Page principale
   ───────────────────────────────────────── */
export default function DiscussionPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [chatInputVal, setChatInputVal] = useState('')

  // États dynamiques du chatbot
  const [, setQuestionActuelle] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [selectedAid, setSelectedAid] = useState(null)

  // ── Hook streaming SSE ──
  const {
    streamingText,
    isThinking,
    isStreaming,
    startStream,
    cancelStream,
  } = useStreamingChat()

  // Dérivé : "en cours d'envoi" = thinking OU streaming
  const sending = isThinking || isStreaming

  const messagesEndRef = useRef(null)

  /* ── Auto-scroll ── */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  // Scroll quand les messages changent, quand on attend, ou quand les suggestions arrivent
  useEffect(() => {
    scrollToBottom()
  }, [messages, isThinking, suggestions, scrollToBottom])

  // Scroll continu pendant l'écriture progressive
  useEffect(() => {
    if (isStreaming) {
      scrollToBottom()
    }
  }, [streamingText, isStreaming, scrollToBottom])

  /* ── Synchroniser la bulle streaming dans messages ── */
  useEffect(() => {
    if (isStreaming && streamingText) {
      setMessages((prev) => {
        const hasStreamingBubble = prev.some((m) => m.id === STREAMING_BUBBLE_ID)
        if (hasStreamingBubble) {
          // Mise à jour additive — pas de reconstruction DOM
          return prev.map((m) =>
            m.id === STREAMING_BUBBLE_ID ? { ...m, text: streamingText } : m
          )
        } else {
          // Première apparition de la bulle IA
          return [
            ...prev,
            {
              id: STREAMING_BUBBLE_ID,
              sender: 'assistant',
              text: streamingText,
              timestamp: null,
              isStreaming: true,
            },
          ]
        }
      })
    }
  }, [streamingText, isStreaming])

  /* ── Charger la conversation ── */
  const loadConversation = useCallback(async () => {
    if (!id) {
      setMessages([])
      setQuestionActuelle(null)
      setSuggestions([])
      setRecommendations([])
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await dashboardService.getHistoryDetail(id)
      const formatted = data.messages.map((m) => ({
        id: m.discussion_id,
        sender: m.expediteur,
        text: m.contenu,
        timestamp: m.date_creation || null,
      }))
      setMessages(formatted)
      setQuestionActuelle(data.question_actuelle)
      setSuggestions(data.suggestions || [])
      setRecommendations(data.aides_recommandees || [])
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    loadConversation()
  }, [loadConversation])

  // Nettoyage : annuler le stream si le composant est démonté
  useEffect(() => {
    return () => {
      cancelStream()
    }
  }, [cancelStream])

  /* ── Envoyer un message (streaming SSE) ── */
  const handleSend = (text) => {
    if (!text.trim() || sending) return

    const now = new Date().toISOString()

    // 1. Afficher immédiatement la bulle utilisateur
    const tempUserMsg = {
      id: Date.now(),
      sender: 'user',
      text,
      timestamp: now,
    }
    setMessages((prev) => [...prev, tempUserMsg])

    // 2. Masquer les anciennes suggestions
    setQuestionActuelle(null)
    setSuggestions([])

    // 3. Démarrer le stream SSE
    startStream(text, id || null, {
      onDone: (metadata) => {
        const finalHistoriqueId = metadata.historique_id

        // Finaliser la bulle streaming → message permanent
        const botMsg = {
          id: metadata.bot_message?.discussion_id ?? Date.now() + 1,
          sender: 'assistant',
          text: metadata.bot_message?.contenu ?? '',
          timestamp: metadata.bot_message?.date_creation ?? new Date().toISOString(),
          isStreaming: false,
        }

        setMessages((prev) =>
          prev
            .filter((m) => m.id !== STREAMING_BUBBLE_ID)
            .concat(botMsg)
        )

        // Mettre à jour suggestions + recommandations depuis le backend
        setQuestionActuelle(metadata.question_actuelle ?? null)
        setSuggestions(metadata.suggestions || [])
        setRecommendations(metadata.aides_recommandees || [])

        // Redirection si nouvelle conversation
        if (!id && finalHistoriqueId) {
          navigate(`/dashboard/discussion/${finalHistoriqueId}`, { replace: true })
        }
      },

      onError: () => {
        // Supprimer la bulle streaming partielle
        setMessages((prev) => prev.filter((m) => m.id !== STREAMING_BUBBLE_ID))

        // Ajouter une bulle d'erreur
        const errorMsg = {
          id: Date.now() + 2,
          sender: 'assistant',
          text: "Impossible de contacter AidFinder IA.",
          isError: true,
          failedText: text,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, errorMsg])
      },
    })
  }

  const handleRetry = (failedText) => {
    // Retirer le message d'erreur
    setMessages((prev) => prev.filter((m) => !m.isError))
    handleSend(failedText)
  }

  const handleSuggestionSelect = (text) => {
    handleSend(text)
  }

  const handleBack = () => navigate(-1)
  const handleNewChat = () => navigate('/dashboard/discussion')

  /* ══════════════════════════════════════════
     États de chargement initial
     ══════════════════════════════════════════ */
  if (loading) {
    return (
      <div className="flex flex-1 flex-col px-4 py-6 sm:px-8">
        <div className="mb-6 flex items-center justify-between border-b border-border/60 pb-4 shrink-0">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="icon"
              onClick={handleBack}
              className="size-9 border-border text-muted-foreground"
            >
              <ArrowLeft className="size-4" />
            </Button>
            <div className="space-y-1">
              <div className="h-4 w-32 bg-muted animate-pulse rounded-md" />
              <div className="h-3 w-48 bg-muted animate-pulse rounded-md" />
            </div>
          </div>
        </div>
        <div className="max-w-3xl mx-auto w-full">
          <ChatMessageSkeleton />
        </div>
      </div>
    )
  }

  /* ══════════════════════════════════════════
     État d'erreur initial (Si le chargement de l'historique plante)
     ══════════════════════════════════════════ */
  if (error) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center p-8 text-center animate-fade-in">
        <div className="rounded-full bg-destructive/10 p-4 text-destructive mb-4">
          <AlertTriangle className="size-7" />
        </div>
        <h3 className="text-base font-bold text-foreground">Erreur de chargement</h3>
        <p className="mt-2 text-sm text-muted-foreground max-w-sm leading-relaxed">
          Impossible de contacter AidFinder IA.
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-3">
          <Button
            onClick={loadConversation}
            className="bg-brand hover:bg-brand-hover text-brand-foreground"
            id="retry-load-btn"
          >
            <RefreshCw className="mr-2 size-4" />
            Réessayer
          </Button>
          <Button variant="outline" onClick={() => navigate('/dashboard')}>
            Retour au tableau de bord
          </Button>
        </div>
      </div>
    )
  }

  /* ══════════════════════════════════════════
     Interface principale
     ══════════════════════════════════════════ */
  return (
    <div className="flex flex-1 flex-col px-4 py-6 sm:px-8">
      {/* En-tête */}
      <div className="mb-5 flex items-center justify-between border-b border-border/60 pb-4 shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <Button
            variant="outline"
            size="icon"
            onClick={handleBack}
            className="size-9 border-border text-muted-foreground hover:bg-muted shrink-0"
            aria-label="Page précédente"
            id="back-btn"
          >
            <ArrowLeft className="size-4" />
          </Button>
          <div className="min-w-0">
            <h2 className="flex items-center gap-1.5 text-sm font-bold text-foreground">
              <Bot className="size-4 text-brand" />
              Assistant IA AidFinder
            </h2>
            <p className="truncate text-xs text-muted-foreground">
              Découvrez vos aides financières en discutant
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Bouton Nouveau Chat */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewChat}
            className="hidden sm:flex items-center gap-1.5 text-xs border-border text-muted-foreground hover:text-brand hover:border-brand/40"
            id="new-chat-header-btn"
          >
            <Plus className="size-3.5" />
            Nouveau chat
          </Button>

          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className="text-xs font-semibold text-brand hover:bg-brand-light"
            id="quit-discussion-btn"
          >
            Quitter
          </Button>
        </div>
      </div>

      {/* Zone de messages */}
      <div className="flex-1 overflow-y-auto pr-1 max-w-3xl mx-auto w-full">
        {messages.length === 0 && !isThinking && !isStreaming ? (
          <EmptyChatState onSelect={handleSuggestionSelect} />
        ) : (
          <div className="space-y-4 py-2">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <div key={msg.id} className="space-y-2">
                  <ConversationBubble
                    msg={msg}
                    isStreaming={msg.id === STREAMING_BUBBLE_ID && isStreaming}
                  />

                  {/* Si le message a échoué, afficher la carte d'erreur élégante */}
                  {msg.isError && (
                    <motion.div
                      variants={messageVariants}
                      initial="hidden"
                      animate="visible"
                      className="ml-10 flex flex-col gap-3 rounded-2xl border border-destructive/20 bg-destructive/5 p-4 max-w-sm shadow-xs"
                    >
                      <div className="flex items-center gap-2 text-destructive">
                        <AlertTriangle className="size-4 shrink-0" />
                        <span className="text-xs font-bold">Impossible de contacter AidFinder IA</span>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleRetry(msg.failedText)}
                        className="w-fit bg-brand hover:bg-brand-hover text-brand-foreground text-xs font-semibold px-4 py-1.5 rounded-lg"
                      >
                        Réessayer
                      </Button>
                    </motion.div>
                  )}
                </div>
              ))}
            </AnimatePresence>

            {/* Indicateur "IA réfléchit" — visible uniquement avant le 1er chunk */}
            <AnimatePresence>
              {isThinking && (
                <motion.div
                  key="typing-indicator"
                  variants={messageVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                >
                  <TypingIndicator />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Suggestions de questions dynamiques — depuis le backend uniquement */}
            {!sending && suggestions && suggestions.length > 0 && (
              <div className="ml-10">
                <SuggestionButtons
                  suggestions={suggestions}
                  onSelect={handleSuggestionSelect}
                />
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Cartes d'aides recommandées */}
        {messages.length > 0 && recommendations && recommendations.length > 0 && (
          <div className="max-w-3xl mx-auto">
            <AidsRecommendedSection
              aids={recommendations}
              historiqueId={id}
              onShowDetail={(aid) => setSelectedAid(aid)}
            />
          </div>
        )}
      </div>

      {/* Zone de saisie */}
      <div className="sticky bottom-0 mt-4 bg-background pt-3 pb-4 shrink-0">
        <ChatInput
          value={chatInputVal}
          onChange={setChatInputVal}
          onSend={handleSend}
          disabled={sending}
        />
      </div>

      {/* Modal de détail d'aide */}
      <AnimatePresence>
        {selectedAid && (
          <AidDetailModal
            aid={selectedAid}
            onClose={() => setSelectedAid(null)}
            onConsult={async () => {
              try {
                if (id) {
                  await dashboardService.recordChatConsultation(id, selectedAid.aide_id)
                } else {
                  await dashboardService.recordAidConsultation(selectedAid.aide_id)
                }
              } catch (err) {
                console.error(err)
              } finally {
                if (selectedAid.url_officielle) {
                  window.open(selectedAid.url_officielle, '_blank', 'noopener,noreferrer')
                }
                setSelectedAid(null)
              }
            }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
