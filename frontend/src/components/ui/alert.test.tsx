import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

describe('Alert', () => {
  it('renders Alert component', () => {
    render(<Alert>Alert content</Alert>);
    expect(screen.getByText('Alert content')).toBeInTheDocument();
  });

  it('renders Alert with variant default', () => {
    render(<Alert>Default Alert</Alert>);
    expect(screen.getByText('Default Alert')).toBeInTheDocument();
  });

  it('renders Alert with destructive variant', () => {
    render(<Alert variant="destructive">Destructive Alert</Alert>);
    expect(screen.getByText('Destructive Alert')).toBeInTheDocument();
  });

  it('renders AlertTitle', () => {
    render(
      <Alert>
        <AlertTitle>Alert Title</AlertTitle>
      </Alert>
    );
    expect(screen.getByText('Alert Title')).toBeInTheDocument();
  });

  it('renders AlertDescription', () => {
    render(
      <Alert>
        <AlertDescription>Alert Description</AlertDescription>
      </Alert>
    );
    expect(screen.getByText('Alert Description')).toBeInTheDocument();
  });

  it('renders complete Alert structure', () => {
    render(
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Warning</AlertTitle>
        <AlertDescription>Something went wrong</AlertDescription>
      </Alert>
    );

    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<Alert className="custom-alert">Content</Alert>);
    expect(screen.getByText('Content')).toHaveClass('custom-alert');
  });

  it('renders with icon', () => {
    render(
      <Alert>
        <AlertCircle />
        <span>With Icon</span>
      </Alert>
    );
    expect(screen.getByText('With Icon')).toBeInTheDocument();
  });
});
