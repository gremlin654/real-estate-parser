import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Label } from '@/components/ui/label';

describe('Label', () => {
  it('renders Label component', () => {
    render(<Label>Label Text</Label>);
    expect(screen.getByText('Label Text')).toBeInTheDocument();
  });

  it('renders with htmlFor attribute', () => {
    render(<Label htmlFor="input">Input Label</Label>);
    expect(screen.getByText('Input Label')).toHaveAttribute('for', 'input');
  });

  it('applies custom className', () => {
    render(<Label className="custom-label">Custom</Label>);
    expect(screen.getByText('Custom')).toHaveClass('custom-label');
  });

  it('renders with children elements', () => {
    render(
      <Label>
        <span>Nested</span>
      </Label>
    );
    expect(screen.getByText('Nested')).toBeInTheDocument();
  });

  it('can be used with form inputs', () => {
    render(
      <div>
        <Label htmlFor="email">Email</Label>
        <input id="email" type="email" />
      </div>
    );

    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveAttribute('id', 'email');
  });
});
