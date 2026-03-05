'use client';

import { Link, useLocation } from 'react-router-dom';
import {
  Sidebar as SidebarUI,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from '@/shared/ui/sidebar';
import { LayoutDashboard, List, PanelLeftClose, PanelLeftOpen, BarChart3, Database } from 'lucide-react';
import { useState } from 'react';

const navigation = [
  { name: 'Панель управления', href: '/', icon: LayoutDashboard },
  { name: 'Объявления', href: '/listings', icon: List },
  { name: 'Статистика', href: '/statistics', icon: BarChart3 },
];

export function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <SidebarUI variant="sidebar" collapsible={collapsed ? 'icon' : 'offcanvas'} className="border-r h-screen flex flex-col">
      <SidebarHeader className="border-b px-4 py-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-primary flex-shrink-0" />
          {!collapsed && (
            <div className="overflow-hidden">
              <h2 className="text-sm font-semibold whitespace-nowrap">Kufar Monitor</h2>
              <p className="text-xs text-muted-foreground whitespace-nowrap">Admin Panel</p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="flex-1 overflow-y-auto">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <SidebarMenuItem key={item.name}>
                    <SidebarMenuButton asChild isActive={isActive} tooltip={item.name}>
                      <Link to={item.href}>
                        <item.icon className="h-4 w-4 flex-shrink-0" />
                        {!collapsed && <span className="truncate">{item.name}</span>}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-3 flex-shrink-0">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center gap-2 p-2 hover:bg-muted rounded-md w-full"
          title={collapsed ? 'Развернуть' : 'Свернуть'}
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4 flex-shrink-0" />
          ) : (
            <>
              <PanelLeftClose className="h-4 w-4 flex-shrink-0" />
              <span className="text-xs text-muted-foreground truncate">Свернуть меню</span>
            </>
          )}
        </button>
      </SidebarFooter>
    </SidebarUI>
  );
}
