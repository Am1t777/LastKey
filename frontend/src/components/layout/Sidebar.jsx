import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Lock, Users, ShieldCheck, Settings, LogOut, Key } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { cn } from '../../lib/utils'

const links = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/secrets', icon: Lock, label: 'Secrets' },
  { to: '/beneficiaries', icon: Users, label: 'Beneficiaries' },
  { to: '/verifier', icon: ShieldCheck, label: 'Verifier' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const { logout, user } = useAuth()
  return (
    <aside className="w-60 min-h-screen bg-card border-r flex flex-col">
      <div className="p-6 border-b">
        <div className="flex items-center gap-2">
          <Key className="h-5 w-5 text-primary" />
          <span className="font-semibold text-lg">LastKey</span>
        </div>
        {user && <p className="text-xs text-muted-foreground mt-1 truncate">{user.email}</p>}
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to}
            className={({ isActive }) => cn(
              'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
              isActive ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
            )}
          >
            <Icon className="h-4 w-4" />{label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t">
        <button onClick={logout} className="flex items-center gap-3 px-3 py-2 w-full rounded-md text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors">
          <LogOut className="h-4 w-4" />Logout
        </button>
      </div>
    </aside>
  )
}
