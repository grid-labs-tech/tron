import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  Home,
  Cloud,
  Globe,
  AppWindow,
  Menu,
  X,
  Shield,
  FileCode,
  LogOut,
  User,
  Settings,
  Users,
  Key,
  Search,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { Logo } from './Logo'
import { useAuth } from '../../contexts/AuthContext'

const generalNavItems = [
  { label: 'Home', path: '/', icon: Home },
  { label: 'Applications', path: '/applications', icon: AppWindow },
]

const adminNavItems = [
  { label: 'Clusters', path: '/clusters', icon: Cloud },
  { label: 'Environments', path: '/environments', icon: Globe },
  { label: 'Templates', path: '/templates', icon: FileCode },
  { label: 'Users', path: '/users', icon: Users },
  { label: 'Tokens', path: '/tokens', icon: Key },
]

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Filtrar itens do menu baseado na pesquisa
  const allNavItems = [...generalNavItems, ...(user?.role === 'admin' ? adminNavItems : [])]
  const filteredGeneralItems = generalNavItems.filter((item) =>
    item.label.toLowerCase().includes(searchQuery.toLowerCase())
  )
  const filteredAdminItems =
    user?.role === 'admin'
      ? adminNavItems.filter((item) => item.label.toLowerCase().includes(searchQuery.toLowerCase()))
      : []

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      const matchedItem = allNavItems.find((item) =>
        item.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
      if (matchedItem) {
        navigate(matchedItem.path)
        setSearchQuery('')
        setSidebarOpen(false)
      }
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="glass-effect-strong fixed top-0 left-0 right-0 z-50 border-b border-neutral-200/80">
        <div className="flex items-center justify-between px-4 py-3 md:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden p-2 rounded-lg text-neutral-600 hover:bg-neutral-100 transition-colors"
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <Logo />
          </div>
          {user && (
            <div className="flex items-center gap-2">
              <div className="hidden md:flex items-center gap-2 text-sm text-neutral-600">
                <User size={16} />
                <span>{user.full_name || user.email}</span>
              </div>
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-neutral-600 hover:bg-neutral-100 transition-colors"
                title="Profile"
              >
                <Settings size={16} />
                <span className="hidden md:inline">Profile</span>
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-neutral-600 hover:bg-neutral-100 transition-colors"
                title="Sair"
              >
                <LogOut size={16} />
                <span className="hidden md:inline">Sair</span>
              </button>
            </div>
          )}
        </div>
      </header>

      <div className="flex flex-1 mt-16">
        {/* Sidebar */}
        <aside
          className={`
            fixed inset-y-0 left-0 z-40
            ${sidebarCollapsed ? 'w-16' : 'w-64'} flex-shrink-0 glass-effect-strong border-r border-neutral-200/80
            transform transition-all duration-300 ease-in-out
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
            pt-16
            overflow-y-auto
            flex flex-col
          `}
        >
          <nav className="p-4 space-y-6 flex-1">
            {/* Barra de Pesquisa */}
            {!sidebarCollapsed && (
              <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                placeholder="Search menu..."
                className="w-full pl-9 pr-3 py-2 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white text-neutral-700 placeholder-neutral-400"
              />
              </div>
            )}

            {/* Menu Geral */}
            <div>
              {!sidebarCollapsed && (
                <div className="flex items-center gap-2 px-3 mb-3">
                  <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                    General
                  </span>
                </div>
              )}
              <ul className="space-y-1.5">
                {filteredGeneralItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path
                  return (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        onClick={() => setSidebarOpen(false)}
                        className={`
                          flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'} px-3 py-2.5 rounded-xl
                          transition-all duration-200
                          ${
                            isActive
                              ? 'bg-gradient-primary text-white shadow-soft font-medium'
                              : 'text-neutral-600 hover:bg-neutral-50 hover:text-primary-600'
                          }
                        `}
                      >
                        <Icon
                          size={sidebarCollapsed ? 22 : 18}
                          className={`${isActive ? 'text-white' : ''} ${sidebarCollapsed ? 'min-w-[22px]' : ''}`}
                        />
                        {!sidebarCollapsed && <span className="text-sm">{item.label}</span>}
                      </Link>
                    </li>
                  )
                })}
              </ul>
            </div>

            {/* Menu Administrativo - Apenas para admins */}
            {user?.role === 'admin' && (
              <div>
                {!sidebarCollapsed && (
                  <div className="flex items-center gap-2 px-3 mb-3">
                    <Shield size={16} className="text-neutral-400" />
                    <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                      Administrative
                    </span>
                  </div>
                )}
                <ul className="space-y-1.5">
                  {filteredAdminItems.map((item) => {
                    const Icon = item.icon
                    const isActive = location.pathname === item.path
                    return (
                      <li key={item.path}>
                        <Link
                          to={item.path}
                          onClick={() => setSidebarOpen(false)}
                          className={`
                            flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'} px-3 py-2.5 rounded-xl
                            transition-all duration-200
                            ${
                              isActive
                                ? 'bg-gradient-primary text-white shadow-soft font-medium'
                                : 'text-neutral-600 hover:bg-neutral-50 hover:text-primary-600'
                            }
                          `}
                        >
                          <Icon
                            size={sidebarCollapsed ? 22 : 18}
                            className={`${isActive ? 'text-white' : ''} ${sidebarCollapsed ? 'min-w-[22px]' : ''}`}
                          />
                          {!sidebarCollapsed && <span className="text-sm">{item.label}</span>}
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}
          </nav>

          {/* Botão de Colapsar */}
          <div className="border-t border-neutral-200/80 mt-auto">
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="w-full flex items-center justify-center gap-3 px-4 py-4 text-neutral-600 hover:bg-neutral-50 hover:text-primary-600 transition-all duration-200"
              title={sidebarCollapsed ? 'Expand menu' : 'Collapse menu'}
            >
              {sidebarCollapsed ? (
                <ChevronRight size={18} />
              ) : (
                <>
                  <ChevronLeft size={18} />
                  <span className="text-sm">Collapse</span>
                </>
              )}
            </button>
          </div>
        </aside>

        {/* Overlay para mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-30 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className={`flex-1 min-w-0 p-6 md:p-8 lg:p-10 pb-24 overflow-x-hidden transition-all duration-300 ${sidebarCollapsed ? 'md:ml-16' : 'md:ml-64'}`}>
          <div className="max-w-7xl mx-auto w-full">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className={`glass-effect-strong border-t border-neutral-200/80 mt-auto transition-all duration-300 ${sidebarCollapsed ? 'md:ml-16' : 'md:ml-64'}`}>
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-sm text-neutral-600">
              <div className="w-4 h-4 bg-gradient-primary rounded"></div>
              <span>© {new Date().getFullYear()} Tron Platform. All rights reserved.</span>
            </div>
            <div className="flex items-center gap-4 text-sm text-neutral-500">
              <span>Version 0.4.0</span>
              <span className="hidden md:inline">•</span>
              <span>Platform as a Service</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
