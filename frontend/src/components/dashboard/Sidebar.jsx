import Logo from '@/src/components/Logo'
import HelpCard from '@/src/components/dashboard/HelpCard'
import SidebarNavItem from '@/src/components/dashboard/SidebarNavItem'

/** Sidebar du dashboard utilisateur */
export default function Sidebar({ basePath = '/dashboard', onNavigate }) {
  return (
    <div className="flex h-full flex-col px-5 py-6 lg:py-8">
      <div className="mb-10 hidden lg:block">
        <Logo linkTo={basePath} />
      </div>

      <nav className="flex flex-col gap-1">
        {/* Nouveau Chat */}
        <SidebarNavItem
          to={`${basePath}/discussion`}
          onClick={() => onNavigate?.()}
        >
          Nouvelle discussion
        </SidebarNavItem>

        {/* Tableau de bord */}
        <SidebarNavItem
          to={basePath}
          end
          onClick={() => onNavigate?.()}
        >
          Tableau de bord
        </SidebarNavItem>

        {/* Profil */}
        <SidebarNavItem
          to={`${basePath}/profil`}
          onClick={() => onNavigate?.()}
        >
          Profil
        </SidebarNavItem>

        {/* Historiques */}
        <SidebarNavItem
          to={`${basePath}/historique`}
          onClick={() => onNavigate?.()}
        >
          Historique
        </SidebarNavItem>

        {/* Aides recommandées */}
        <SidebarNavItem
          to={`${basePath}/aides-recommandees`}
          onClick={() => onNavigate?.()}
        >
          Aides recommandées
        </SidebarNavItem>

      </nav>

      <div className="mt-auto pt-8">
        <HelpCard />
      </div>
    </div>
  )
}
