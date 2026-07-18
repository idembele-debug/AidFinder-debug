import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import Logo from '@/src/components/Logo'

/** Structure responsive partagée entre les dashboards utilisateur et admin */
export default function DashboardShell({
  basePath,
  sidebar,
  dimmed = false,
  headerExtra,
  dialog,
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const closeSidebar = () => setSidebarOpen(false)

  return (
    <div className="flex min-h-screen bg-background">
      {dialog}

      {sidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={closeSidebar}
          aria-label="Fermer le menu"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 transform bg-sidebar transition-transform duration-300 lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between px-5 lg:hidden">
          <Logo linkTo={basePath} />
          <button type="button" onClick={closeSidebar} className="text-sidebar-foreground" aria-label="Fermer">
            <X className="size-5" />
          </button>
        </div>
        {sidebar({ onNavigate: closeSidebar })}
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-border px-4 lg:hidden">
          <div className="flex items-center">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="mr-3 text-foreground"
              aria-label="Ouvrir le menu"
            >
              <Menu className="size-5" />
            </button>
            <Logo linkTo={basePath} />
          </div>
          {headerExtra}
        </header>

        <main
          className={`flex flex-1 flex-col transition-opacity duration-300 ${
            dimmed ? 'pointer-events-none opacity-40' : ''
          }`}
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}
