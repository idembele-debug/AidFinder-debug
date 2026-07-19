import Sidebar from '@/src/components/dashboard/Sidebar'
import DashboardShell from '@/src/components/dashboard/DashboardShell'
import ProfileCompletionDialog from '@/src/components/profile/ProfileCompletionDialog'
import { ProfileProvider, useProfile } from '@/src/contexts/ProfileContext'

const BASE_PATH = '/dashboard'

function UserDashboardContent() {
  const { loading, isProfileComplete } = useProfile()

  return (
    <DashboardShell
      basePath={BASE_PATH}
      dimmed={!loading && !isProfileComplete}
      dialog={<ProfileCompletionDialog />}
      sidebar={({ onNavigate }) => (
        <Sidebar
          basePath={BASE_PATH}
          onNavigate={onNavigate}
        />
      )}
    />
  )
}

/** Layout du dashboard utilisateur */
export default function DashboardLayout() {
  return (
    <ProfileProvider>
      <UserDashboardContent />
    </ProfileProvider>
  )
}
