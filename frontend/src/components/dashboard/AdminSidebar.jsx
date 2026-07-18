import { useNavigate } from 'react-router-dom'
import { LayoutDashboard, Users, FileText, BarChart2, UserCircle, LogOut } from 'lucide-react'
import { cn } from '@/lib/utils'
import Logo from '@/src/components/Logo'
import SidebarNavItem from '@/src/components/dashboard/SidebarNavItem'
import { useAuth } from '@/src/contexts/AuthContext'

const NAV_LINKS = [
  { label: 'Tableau de bord', to: '', icon: LayoutDashboard, end: true },
  { label: 'Utilisateurs', to: 'utilisateurs', icon: Users },
  { label: 'Aides', to: 'aides', icon: FileText },
  { label: 'Statistiques', to: 'statistiques', icon: BarChart2 },
  { label: 'Profil', to: 'profil', icon: UserCircle },
]

/** Sidebar du dashboard administrateur */
export default function AdminSidebar({ basePath = '/admin', onNavigate }) {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    onNavigate?.()
    navigate('/')
  }

  return (
    <div className="flex h-full flex-col px-5 py-6 lg:py-8">
      <div className="mb-10 hidden lg:block">
        <Logo linkTo={basePath} />
      </div>

      {/* Navigation principale */}
      <nav className="flex flex-1 flex-col gap-1">
        {NAV_LINKS.map((item) => (
          <SidebarNavItem
            key={item.label}
            to={item.to ? `${basePath}/${item.to}` : basePath}
            end={item.end}
            onClick={() => onNavigate?.()}
            icon={item.icon}
          >
            {item.label}
          </SidebarNavItem>
        ))}
      </nav>

      {/* Actions du bas */}
      <div className="mt-6 border-t border-sidebar-border pt-4 space-y-1">
        {/* Déconnexion */}
        <button
          type="button"
          onClick={handleLogout}
          className={cn(
            'flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-left text-sm text-sidebar-foreground',
            'transition-all duration-200 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
          )}
        >
          <LogOut className="size-4 shrink-0" />
          Déconnexion
        </button>


      </div>
    </div>
  )
}
