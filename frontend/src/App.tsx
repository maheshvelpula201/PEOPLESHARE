
import { useState } from 'react'
import LoginPage from './pages/LoginPage'
import AppLayout from './components/layout/AppLayout'
import './App.css'

type AppPage =
  | 'home'
  | 'employees'
  | 'departments'
  | 'organization'
  | 'attendance'
  | 'attendance-history'
  | 'leave-requests'
  | 'leave-history'
  | 'announcements'
  | 'company-updates'
  | 'profile'
  | 'settings'

const pageDetails: Record<AppPage, { title: string; description: string }> = {
  home: {
    title: 'Welcome to PeopleSphere',
    description: 'Your company workspace, all in one place.',
  },
  employees: {
    title: 'Employees',
    description: 'Employee management will be connected in a later batch.',
  },
  departments: {
    title: 'Departments',
    description: 'Department management will be connected in a later batch.',
  },
  organization: {
    title: 'Organization',
    description: 'Your company organization structure will appear here.',
  },
  attendance: {
    title: 'Attendance',
    description: 'Attendance integration is pending.',
  },
  'attendance-history': {
    title: 'Attendance History',
    description: 'Attendance history integration is pending.',
  },
  'leave-requests': {
    title: 'Leave Requests',
    description: 'Leave request integration is pending.',
  },
  'leave-history': {
    title: 'Leave History',
    description: 'Leave history integration is pending.',
  },
  announcements: {
    title: 'Announcements',
    description: 'Company announcements integration is pending.',
  },
  'company-updates': {
    title: 'Company Updates',
    description: 'Company updates integration is pending.',
  },
  profile: {
    title: 'My Profile',
    description: 'Your account information will appear here.',
  },
  settings: {
    title: 'Account Settings',
    description: 'Account settings integration is pending.',
  },
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [activePage, setActivePage] = useState<AppPage>('home')

  // Temporary frontend-only handler.
  // Real authentication will be connected in the next batch.
  async function handleLogin(
    _companyId: string,
    _email: string,
    _password: string,
  ) {
    throw new Error(
      'The login page is ready. Backend authentication will be connected next.',
    )
  }

  if (!isAuthenticated) {
    return (
      <LoginPage
        onLogin={handleLogin}
        onRegister={() => {
          window.alert('Company registration will be connected next.')
        }}
      />
    )
  }

  const currentPage = pageDetails[activePage]

  const demoUser = {
    userId: 0,
    companyId: 0,
    email: 'preview@peoplesphere.local',
    role: 'company_admin',
  }

  return (
    <AppLayout
      user={demoUser}
      activePage={activePage}
      onNavigate={setActivePage}
      onLogout={() => {
        setIsAuthenticated(false)
        setActivePage('home')
      }}
    >
      <main className="page-content">
        <div className="page-heading">
          <p className="page-eyebrow">PEOPLESPHERE WORKSPACE</p>
          <h1>{currentPage.title}</h1>
          <p>{currentPage.description}</p>
        </div>

        {activePage === 'home' && (
          <section className="home-welcome">
            <div>
              <p className="home-welcome-label">YOUR WORKSPACE</p>
              <h2>Everything starts here.</h2>
              <p>
                Navigate through your company's people, attendance,
                leave management and communications.
              </p>
            </div>
          </section>
        )}

        {activePage !== 'home' && (
          <section className="page-placeholder">
            <h2>{currentPage.title}</h2>
            <p>{currentPage.description}</p>
            <span>Feature integration pending</span>
          </section>
        )}
      </main>
    </AppLayout>
  )
}

export default App
