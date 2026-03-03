import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AppLayout } from './AppLayout';
import { MemoryRouter } from 'react-router-dom';

// Mock Sidebar
vi.mock('./Layout', () => ({
  AppSidebar: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="sidebar">{children}</div>
  ),
}));

const createWrapper = (initialRoute = '/') => {
  return ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={[initialRoute]}>{children}</MemoryRouter>
  );
};

describe('AppLayout', () => {
  it('renders AppLayout with children', () => {
    render(
      <AppLayout>
        <div>Page Content</div>
      </AppLayout>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Page Content')).toBeInTheDocument();
  });

  it('renders Sidebar', () => {
    render(
      <AppLayout>
        <div>Content</div>
      </AppLayout>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('renders children inside layout', () => {
    render(
      <AppLayout>
        <main>Main Content</main>
      </AppLayout>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Main Content')).toBeInTheDocument();
  });

  it('renders with multiple children', () => {
    render(
      <AppLayout>
        <header>Header</header>
        <main>Main</main>
        <footer>Footer</footer>
      </AppLayout>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Header')).toBeInTheDocument();
    expect(screen.getByText('Main')).toBeInTheDocument();
    expect(screen.getByText('Footer')).toBeInTheDocument();
  });
});
