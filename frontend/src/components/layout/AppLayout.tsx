import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'

export type AppPage =
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

type AppUser = {
  userId: number
  companyId: number
  email: string
  role: string
}

type AppLayoutProps = {
  user: AppUser
  activePage: AppPage
  onNavigate: (page: AppPage) => void
  onLogout: () => void
  children: ReactNode
}

const navigation = [
  {
    heading: 'WORKSPACE',
    items: [{ id: 'home', label: 'Home', icon: '⌂' }],
  },
  {
    heading: 'PEOPLE MANAGEMENT',
    items: [
      { id: 'employees', label: 'Employees', icon: '♙' },
      { id: 'departments', label: 'Departments', icon: '▦' },
      { id: 'organization', label: 'Organization', icon: '⌘' },
    ],
  },
  {
    heading: 'ATTENDANCE',
    items: [
      { id: 'attendance', label: 'Attendance', icon: '◷' },
      { id: 'attendance-history', label: 'Attendance History', icon: '◴' },
    ],
  },
  {
    heading: 'LEAVE MANAGEMENT',
    items: [
      { id: 'leave-requests', label: 'Leave Requests', icon: '▤' },
      { id: 'leave-history', label: 'Leave History', icon: '▧' },
    ],
  },
  {
    heading: 'COMMUNICATION',
    items: [
      { id: 'announcements', label: 'Announcements', icon: '◉' },
      { id: 'company-updates', label: 'Company Updates', icon: '▱' },
    ],
  },
] satisfies {
  heading: string
  items: { id: AppPage; label: string; icon: string }[]
}[]

const pageLabels: Record<AppPage, string> = {
  home: 'Home',
  employees: 'Employees',
  departments: 'Departments',
  organization: 'Organization',
  attendance: 'Attendance',
  'attendance-history': 'Attendance History',
  'leave-requests': 'Leave Requests',
  'leave-history': 'Leave History',
  announcements: 'Announcements',
  'company-updates': 'Company Updates',
  profile: 'My Profile',
  settings: 'Account Settings',
}

function getInitials(email: string) {
  const name = email.split('@')[0] || 'U'
  return name.slice(0, 2).toUpperCase()
}

function formatRole(role: string) {
  return role
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export default function AppLayout({
  user,
  activePage,
  onNavigate,
  onLogout,
  children,
}: AppLayoutProps) {
  const [search, setSearch] = useState('')
  const [profileOpen, setProfileOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const filteredNavigation = useMemo(() => {
    const query = search.trim().toLowerCase()

    if (!query) return navigation

    return navigation
      .map((group) => ({
        ...group,
        items: group.items.filter((item) =>
          item.label.toLowerCase().includes(query),
        ),
      }))
      .filter((group) => group.items.length > 0)
  }, [search])

  function navigate(page: AppPage) {
    onNavigate(page)
    setMobileOpen(false)
    setProfileOpen(false)
  }

  return (
    <div className="app-shell">
      {mobileOpen && (
        <button
          className="mobile-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside className={`app-sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-top-space" />

        <div className="sidebar-brand">
          <div className="brand-mark">P</div>
          <div className="brand-name">
            <strong>PeopleSphere</strong>
            <span>WORKSPACE</span>
          </div>
          <button
            className="mobile-close"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            ×
          </button>
        </div>

        <div className="sidebar-search">
          <span aria-hidden="true">⌕</span>
          <input
            type="search"
            placeholder="Search features..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label="Search features"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              aria-label="Clear search"
            >
              ×
            </button>
          )}
        </div>

        <nav className="sidebar-navigation" aria-label="Main navigation">
          {filteredNavigation.length === 0 ? (
            <div className="search-empty">
              No features found for "{search}"
            </div>
          ) : (
            filteredNavigation.map((group) => (
              <section className="nav-group" key={group.heading}>
                <h2>{group.heading}</h2>
                {group.items.map((item) => (
                  <button
                    key={item.id}
                    className={`nav-item ${
                      activePage === item.id ? 'active' : ''
                    }`}
                    onClick={() => navigate(item.id)}
                  >
                    <span className="nav-icon" aria-hidden="true">
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                    {activePage === item.id && (
                      <span className="active-indicator" />
                    )}
                  </button>
                ))}
              </section>
            ))
          )}
        </nav>

        <div className="sidebar-profile">
          {profileOpen && (
            <div className="profile-menu">
              <button onClick={() => navigate('profile')}>
                <span>♙</span> My Profile
              </button>
              <button onClick={() => navigate('settings')}>
                <span>⚙</span> Account Settings
              </button>
              <div className="profile-menu-divider" />
              <button className="logout-option" onClick={onLogout}>
                <span>↪</span> Log out
              </button>
            </div>
          )}

          <button
            className="profile-trigger"
            onClick={() => setProfileOpen((open) => !open)}
            aria-expanded={profileOpen}
          >
            <div className="profile-avatar">{getInitials(user.email)}</div>
            <div className="profile-identity">
              <strong>{user.email.split('@')[0]}</strong>
              <span>{formatRole(user.role)}</span>
            </div>
            <span className="profile-chevron">
              {profileOpen ? '⌃' : '⌄'}
            </span>
          </button>
        </div>
      </aside>

      <main className="app-main">
        <header className="app-topbar">
          <button
            className="mobile-menu-button"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            ☰
          </button>
          <div className="topbar-breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-separator">/</span>
            <strong>{pageLabels[activePage]}</strong>
          </div>
          <div className="topbar-company">
            Company ID&nbsp; #{user.companyId}
          </div>
        </header>

        <div className="app-content">{children}</div>
      </main>
    </div>
  )
}