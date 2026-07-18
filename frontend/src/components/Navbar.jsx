import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import Logo from '@/src/components/Logo'

/** Barre de navigation pour les pages publiques (Home, Login, Register) */
export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Logo />

        <nav className="flex items-center gap-2 sm:gap-3">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/login">Connexion</Link>
          </Button>
          <Button size="sm" className="bg-primary hover:bg-primary/90 text-primary-foreground" asChild>
            <Link to="/register">S&apos;inscrire</Link>
          </Button>
        </nav>
      </div>
    </header>
  )
}
