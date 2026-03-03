import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Input } from '@/components/ui/input';
import { userEvent } from '@testing-library/user-event';

describe('Input', () => {
  it('renders input element', () => {
    render(<Input />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders with placeholder', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('renders with value and onChange', () => {
    const { container } = render(<Input value="Test value" onChange={() => {}} />);
    expect(container.querySelector('input')).toHaveValue('Test value');
  });

  it('can be disabled', () => {
    render(<Input disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('can be read-only', () => {
    render(<Input readOnly />);
    expect(screen.getByRole('textbox')).toHaveAttribute('readonly');
  });

  it('calls onChange handler', async () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);
    
    await userEvent.type(screen.getByRole('textbox'), 'test');
    expect(handleChange).toHaveBeenCalledTimes(4);
  });

  it('can have type email', () => {
    render(<Input type="email" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('type', 'email');
  });

  it('can have type number', () => {
    render(<Input type="number" />);
    expect(screen.getByRole('spinbutton')).toHaveAttribute('type', 'number');
  });

  it('applies custom className', () => {
    render(<Input className="custom-input" />);
    expect(screen.getByRole('textbox')).toHaveClass('custom-input');
  });

  it('can have custom id', () => {
    render(<Input id="test-input" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('id', 'test-input');
  });

  it('can have name attribute', () => {
    render(<Input name="testName" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('name', 'testName');
  });

  it('can have required attribute', () => {
    render(<Input required />);
    expect(screen.getByRole('textbox')).toHaveAttribute('required');
  });
});
