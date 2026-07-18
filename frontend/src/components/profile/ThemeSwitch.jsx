import { Sun, Moon } from 'lucide-react'
import { useTheme } from '@/src/contexts/ThemeContext'

/**
 * Composant Switch pour le thème Light/Dark
 * Design moderne intégré à AidFinder
 */
export default function ThemeSwitch() {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className="relative inline-flex h-7 w-14 items-center rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-brand/50"
      style={{
        backgroundColor: theme === 'dark' ? 'var(--brand)' : 'var(--muted)',
      }}
      aria-label={theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
    >
      {/* Icône soleil (visible en mode dark) */}
      {theme === 'dark' && (
        <Sun className="absolute left-1.5 size-4 text-brand-foreground transition-opacity duration-300" />
      )}

      {/* Icône lune (visible en mode light) */}
      {theme === 'light' && (
        <Moon className="absolute right-1.5 size-4 text-brand transition-opacity duration-300" />
      )}

      {/* Bouton glissant */}
      <span
        className="inline-block size-5 transform rounded-full bg-background shadow-md transition-transform duration-300"
        style={{
          transform: theme === 'dark' ? 'translateX(28px)' : 'translateX(4px)',
        }}
      />
    </button>
  )
}
