'use client';

import { Link, useLocation } from 'react-router-dom';
import { Home, List, Settings, BarChart3, Menu, Database, TrendingDown, Star } from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from '@/shared/ui/sheet';
import { Button } from '@/shared/ui/button';
import { useState, ReactNode } from 'react';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/', icon: Home, label: 'Панель управления' },
    { path: '/listings', icon: List, label: 'Объявления' },
    { path: '/favorites', icon: Star, label: 'Избранные' },
    { path: '/deals', icon: TrendingDown, label: 'Выгодные предложения' },
    { path: '/price-drops', icon: TrendingDown, label: '📉 Price Drop' },
    { path: '/statistics', icon: BarChart3, label: 'Статистика' },
    { path: '/analytics/price-per-m2', icon: BarChart3, label: 'Аналитика цены за м²' },
    { path: '/settings', icon: Settings, label: 'Настройки' },
  ];

  const NavContent = ({ mobile = false }: { mobile?: boolean }) => (
    <>
      <div className={`mb-8 ${mobile ? 'mt-4' : ''}`}>
        <div className="flex items-center gap-2">
          <Database className="h-6 w-6 text-primary" />
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Kufar Monitor
            </h1>
            <p className="text-xs text-muted-foreground">Admin Panel</p>
          </div>
        </div>
      </div>
      <nav className="space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => mobile && setIsMobileMenuOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'bg-gradient-to-r from-primary to-accent text-white shadow-lg shadow-primary/25'
                  : 'hover:bg-secondary/50 hover:translate-x-1'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-muted-foreground group-hover:text-primary'} transition-colors`} />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:block w-72 bg-card border-r p-6 sticky top-0 h-screen overflow-y-auto animate-slide-in">
        <NavContent />
      </aside>

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-card/80 backdrop-blur-lg border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-primary" />
          <span className="font-semibold">Kufar Monitor</span>
        </div>
        <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" className="lg:hidden h-10 w-10 p-0">
              <Menu className="w-6 h-6" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 p-6">
            <NavContent mobile />
          </SheetContent>
        </Sheet>
      </div>

      {/* Main Content */}
      <main className="flex-1 p-4 md:p-6 lg:p-8 mt-14 lg:mt-0">
        <div className="max-w-7xl mx-auto animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
