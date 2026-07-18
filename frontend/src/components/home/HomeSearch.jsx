import { useEffect, useState } from 'react'
import { Loader2, Search, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import homeService from '@/src/services/home'
import AidCard from '@/src/components/home/AidCard'
import { getApiErrorMessage } from '@/src/utils/errors'

const DEBOUNCE_MS = 350

/** Barre de recherche avec résultats instantanés via GET /api/home/search. */
export default function HomeSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [hasSearched, setHasSearched] = useState(false)

  useEffect(() => {
    const trimmed = query.trim()
    if (!trimmed) {
      setResults([])
      setError('')
      setHasSearched(false)
      setLoading(false)
      return
    }

    setLoading(true)
    setError('')

    const timer = setTimeout(async () => {
      try {
        const data = await homeService.searchAids(trimmed)
        setResults(data)
        setHasSearched(true)
      } catch (err) {
        setResults([])
        setError(getApiErrorMessage(err, 'La recherche a échoué.'))
        setHasSearched(true)
      } finally {
        setLoading(false)
      }
    }, DEBOUNCE_MS)

    return () => clearTimeout(timer)
  }, [query])

  const clearSearch = () => {
    setQuery('')
    setResults([])
    setError('')
    setHasSearched(false)
  }

  return (
    <div className="space-y-8">
      <div className="relative mx-auto max-w-2xl">
        <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Rechercher une aide par mot-clé…"
          className="h-12 rounded-xl border-border/60 bg-background pl-12 pr-12 text-base shadow-sm"
          aria-label="Rechercher une aide"
        />
        {query && (
          <button
            type="button"
            onClick={clearSearch}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Effacer la recherche"
          >
            <X className="size-4" />
          </button>
        )}
        {loading && (
          <Loader2 className="absolute right-10 top-1/2 size-4 -translate-y-1/2 animate-spin text-brand" />
        )}
      </div>

      {error && (
        <p className="text-center text-sm text-destructive">{error}</p>
      )}

      {hasSearched && !loading && !error && results.length === 0 && (
        <p className="text-center text-muted-foreground">
          Aucune aide ne correspond à votre recherche.
        </p>
      )}

      {results.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((aide) => (
            <AidCard key={aide.aide_id} aide={aide} />
          ))}
        </div>
      )}
    </div>
  )
}
