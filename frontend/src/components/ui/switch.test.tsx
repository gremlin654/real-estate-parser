import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Switch } from '@/components/ui/switch';
import { userEvent } from '@testing-library/user-event';

describe('Switch', () => {
  it('renders Switch component', () => {
    render(<Switch />);
    expect(screen.getByRole('switch')).toBeInTheDocument();
  });

  it('renders unchecked by default', () => {
    render(<Switch />);
    expect(screen.getByRole('switch')).not.toBeChecked();
  });

  it('renders checked when checked prop is true', () => {
    render(<Switch checked />);
    expect(screen.getByRole('switch')).toBeChecked();
  });

  it('can be disabled', () => {
    render(<Switch disabled />);
    expect(screen.getByRole('switch')).toBeDisabled();
  });

  it('calls onCheckedChange when clicked', async () => {
    const handleCheckedChange = vi.fn();
    render(<Switch onCheckedChange={handleCheckedChange} />);
    
    await userEvent.click(screen.getByRole('switch'));
    expect(handleCheckedChange).toHaveBeenCalledWith(true);
  });

  it('calls onCheckedChange with false when unchecked', async () => {
    const handleCheckedChange = vi.fn();
    render(<Switch checked onCheckedChange={handleCheckedChange} />);
    
    await userEvent.click(screen.getByRole('switch'));
    expect(handleCheckedChange).toHaveBeenCalledWith(false);
  });

  it('applies custom className', () => {
    render(<Switch className="custom-switch" />);
    expect(screen.getByRole('switch')).toHaveClass('custom-switch');
  });

  it('has id attribute', () => {
    render(<Switch id="test-switch" />);
    expect(screen.getByRole('switch')).toHaveAttribute('id', 'test-switch');
  });

  it('can be used with label', () => {
    render(
      <div>
        <label htmlFor="switch">Enable feature</label>
        <Switch id="switch" />
      </div>
    );

    expect(screen.getByText('Enable feature')).toBeInTheDocument();
    expect(screen.getByRole('switch')).toHaveAttribute('id', 'switch');
  });
});
