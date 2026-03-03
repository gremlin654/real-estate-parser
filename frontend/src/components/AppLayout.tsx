import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, List, Settings, BarChart3 } from 'lucide-react';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Home, label: 'Панель управления' },
    { path: '/listings', icon: List, label: 'Объявления' },
    { path: '/statistics', icon: BarChart3, label: 'Статистика' },
    { path: '/settings', icon: Settings, label: 'Настройки' },
  ];

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-card border-r p-4">
        <div className="mb-8">
          <h1 className="text-xl font-bold">Kufar Monitor</h1>
          <p className="text-sm text-muted-foreground">Admin Panel</p>
        </div>
        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
