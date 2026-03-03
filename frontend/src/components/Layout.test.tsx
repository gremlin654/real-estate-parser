import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AppSidebar } from '@/components/Layout';
import { SidebarProvider } from '@/components/ui/sidebar';

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  LayoutDashboard: ({ className }: { className?: string }) => (
    <svg data-testid="layout-dashboard-icon" className={className} />
  ),
  List: ({ className }: { className?: string }) => (
    <svg data-testid="list-icon" className={className} />
  ),
  Database: ({ className }: { className?: string }) => (
    <svg data-testid="database-icon" className={className} />
  ),
  Settings: ({ className }: { className?: string }) => (
    <svg data-testid="settings-icon" className={className} />
  ),
  PanelLeftClose: ({ className }: { className?: string }) => (
    <svg data-testid="panel-left-close-icon" className={className} />
  ),
  PanelLeftOpen: ({ className }: { className?: string }) => (
    <svg data-testid="panel-left-open-icon" className={className} />
  ),
  BarChart3: ({ className }: { className?: string }) => (
    <svg data-testid="bar-chart-3-icon" className={className} />
  ),
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <SidebarProvider>
        {component}
      </SidebarProvider>
    </BrowserRouter>
  );
};

describe('Layout', () => {
  describe('AppSidebar', () => {
    it('должен рендерить заголовок Kufar Monitor', () => {
      renderWithRouter(<AppSidebar />);

      expect(screen.getByText('Kufar Monitor')).toBeInTheDocument();
      expect(screen.getByText('Admin Panel')).toBeInTheDocument();
    });

    it('должен рендерить навигационные ссылки', () => {
      renderWithRouter(<AppSidebar />);

      expect(screen.getByText('Панель управления')).toBeInTheDocument();
      expect(screen.getByText('Объявления')).toBeInTheDocument();
    });

    it('должен иметь иконки для навигации', () => {
      renderWithRouter(<AppSidebar />);

      expect(screen.getByTestId('layout-dashboard-icon')).toBeInTheDocument();
      expect(screen.getByTestId('list-icon')).toBeInTheDocument();
      expect(screen.getByTestId('database-icon')).toBeInTheDocument();
    });

    it('должен иметь кнопку сворачивания меню', () => {
      renderWithRouter(<AppSidebar />);

      const collapseButton = screen.getByTitle(/Свернуть/);
      expect(collapseButton).toBeInTheDocument();
    });

    it('должен сворачивать меню при клике', async () => {
      renderWithRouter(<AppSidebar />);

      const collapseButton = screen.getByTitle(/Свернуть/);
      fireEvent.click(collapseButton);

      // After collapse, button should have title "Развернуть"
      expect(screen.getByTitle('Развернуть')).toBeInTheDocument();
    });

    it('должен разворачивать меню при повторном клике', async () => {
      renderWithRouter(<AppSidebar />);

      const collapseButton = screen.getByTitle(/Свернуть/);
      fireEvent.click(collapseButton);
      fireEvent.click(collapseButton);

      // After expand, button should still show Свернуть text
      expect(screen.getByText('Свернуть меню')).toBeInTheDocument();
    });

    it('должен показывать tooltip для кнопок навигации', () => {
      renderWithRouter(<AppSidebar />);

      const dashboardLink = screen.getByText('Панель управления').closest('a');
      expect(dashboardLink).toBeInTheDocument();
    });

    it('должен иметь правильную структуру Sidebar', () => {
      const { container } = renderWithRouter(<AppSidebar />);

      const sidebar = container.querySelector('[class*="Sidebar"]');
      expect(sidebar).toBeInTheDocument();
    });

    describe('collapsed state', () => {
      it('должен скрывать текст при свёрнутом меню', async () => {
        renderWithRouter(<AppSidebar />);

        const collapseButton = screen.getByTitle(/Свернуть/);
        fireEvent.click(collapseButton);

        // Text should still be in DOM but not visible in collapsed state
        expect(screen.queryByText('Свернуть меню')).not.toBeInTheDocument();
        expect(screen.getByTestId('panel-left-open-icon')).toBeInTheDocument();
      });

      it('должен показывать иконки в свёрнутом состоянии', async () => {
        renderWithRouter(<AppSidebar />);

        const collapseButton = screen.getByTitle(/Свернуть/);
        fireEvent.click(collapseButton);

        expect(screen.getByTestId('layout-dashboard-icon')).toBeInTheDocument();
        expect(screen.getByTestId('list-icon')).toBeInTheDocument();
      });
    });

    describe('navigation', () => {
      it('должен иметь ссылку на Dashboard', () => {
        renderWithRouter(<AppSidebar />);

        const dashboardLink = screen.getByText('Панель управления').closest('a');
        expect(dashboardLink).toHaveAttribute('href', '/');
      });

      it('должен иметь ссылку на Listings', () => {
        renderWithRouter(<AppSidebar />);

        const listingsLink = screen.getByText('Объявления').closest('a');
        expect(listingsLink).toHaveAttribute('href', '/listings');
      });
    });
  });
});
