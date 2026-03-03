import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RoomsFilter } from './rooms-filter';

describe('RoomsFilter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const defaultProps = {
    selectedRooms: [],
    selectedOther: false,
    onRoomsChange: vi.fn(),
    onOtherChange: vi.fn(),
  };

  it('renders RoomsFilter button', () => {
    render(<RoomsFilter {...defaultProps} />);
    expect(screen.getByText('Комнаты')).toBeInTheDocument();
  });

  it('opens popover when button is clicked', async () => {
    const user = userEvent.setup();
    render(<RoomsFilter {...defaultProps} />);

    await user.click(screen.getByText('Комнаты'));
    await waitFor(() => {
      expect(screen.getByText('1 комната')).toBeInTheDocument();
    });
  });

  it('displays room options in popover', async () => {
    const user = userEvent.setup();
    render(<RoomsFilter {...defaultProps} />);

    await user.click(screen.getByText('Комнаты'));

    await waitFor(() => {
      expect(screen.getByText('1 комната')).toBeInTheDocument();
      expect(screen.getByText('2 комнаты')).toBeInTheDocument();
      expect(screen.getByText('3 комнаты')).toBeInTheDocument();
      expect(screen.getByText('4 комнаты')).toBeInTheDocument();
    });
  });

  it('displays "Другие" option', async () => {
    const user = userEvent.setup();
    render(<RoomsFilter {...defaultProps} />);

    await user.click(screen.getByText('Комнаты'));

    await waitFor(() => {
      expect(screen.getByText('Другие (5+, студия)')).toBeInTheDocument();
    });
  });

  it('calls onRoomsChange when room is selected', async () => {
    const user = userEvent.setup();
    const mockOnRoomsChange = vi.fn();
    render(<RoomsFilter {...defaultProps} onRoomsChange={mockOnRoomsChange} />);

    await user.click(screen.getByText('Комнаты'));
    await waitFor(() => {
      expect(screen.getByText('1 комната')).toBeInTheDocument();
    });

    await user.click(screen.getByText('1 комната'));
    expect(mockOnRoomsChange).toHaveBeenCalledWith([1]);
  });

  it('calls onRoomsChange when room is deselected', async () => {
    const user = userEvent.setup();
    const mockOnRoomsChange = vi.fn();
    render(
      <RoomsFilter
        {...defaultProps}
        selectedRooms={[1, 2]}
        onRoomsChange={mockOnRoomsChange}
      />
    );

    await user.click(screen.getByText('2 комн.'));
    await waitFor(() => {
      expect(screen.getByText('1 комната')).toBeInTheDocument();
    });

    await user.click(screen.getByText('1 комната'));
    expect(mockOnRoomsChange).toHaveBeenCalledWith([2]);
  });

  it('calls onOtherChange when "Другие" is selected', async () => {
    const user = userEvent.setup();
    const mockOnOtherChange = vi.fn();
    render(<RoomsFilter {...defaultProps} onOtherChange={mockOnOtherChange} />);

    await user.click(screen.getByText('Комнаты'));
    await waitFor(() => {
      expect(screen.getByText('Другие (5+, студия)')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Другие (5+, студия)'));
    expect(mockOnOtherChange).toHaveBeenCalledWith(true);
  });

  it('displays reset button when rooms are selected', async () => {
    const user = userEvent.setup();
    render(<RoomsFilter {...defaultProps} selectedRooms={[1]} />);

    await user.click(screen.getByText('1 комн.'));
    await waitFor(() => {
      expect(screen.getByText('Сброс')).toBeInTheDocument();
    });
  });

  it('calls clearAll when reset button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnRoomsChange = vi.fn();
    const mockOnOtherChange = vi.fn();
    render(
      <RoomsFilter
        {...defaultProps}
        selectedRooms={[1, 2]}
        selectedOther={true}
        onRoomsChange={mockOnRoomsChange}
        onOtherChange={mockOnOtherChange}
      />
    );

    await user.click(screen.getByText('2+ комн.'));
    await waitFor(() => {
      expect(screen.getByText('Сброс')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Сброс'));
    expect(mockOnRoomsChange).toHaveBeenCalledWith([]);
    expect(mockOnOtherChange).toHaveBeenCalledWith(false);
  });

  it('displays selection count in button', () => {
    render(<RoomsFilter {...defaultProps} selectedRooms={[1, 2, 3]} />);
    expect(screen.getByText('3 комн.')).toBeInTheDocument();
  });

  it('displays selection count with plus when other is selected', () => {
    render(
      <RoomsFilter
        {...defaultProps}
        selectedRooms={[1, 2]}
        selectedOther={true}
      />
    );
    expect(screen.getByText('2+ комн.')).toBeInTheDocument();
  });

  it('toggles multiple rooms', async () => {
    const user = userEvent.setup();
    const mockOnRoomsChange = vi.fn();
    render(
      <RoomsFilter
        {...defaultProps}
        selectedRooms={[1]}
        onRoomsChange={mockOnRoomsChange}
      />
    );

    await user.click(screen.getByText('1 комн.'));
    await waitFor(() => {
      expect(screen.getByText('2 комнаты')).toBeInTheDocument();
    });

    await user.click(screen.getByText('2 комнаты'));
    expect(mockOnRoomsChange).toHaveBeenCalledWith([1, 2]);
  });

  it('closes popover when clicking outside', async () => {
    const user = userEvent.setup();
    render(<RoomsFilter {...defaultProps} />);

    await user.click(screen.getByText('Комнаты'));
    await waitFor(() => {
      expect(screen.getByText('1 комната')).toBeInTheDocument();
    });

    await user.click(document.body);
    await waitFor(() => {
      expect(screen.queryByText('1 комната')).not.toBeInTheDocument();
    });
  });

  it('applies selected state styling to selected rooms', async () => {
    const user = userEvent.setup();
    render(<RoomsFilter {...defaultProps} selectedRooms={[1]} />);

    await user.click(screen.getByText('1 комн.'));
    await waitFor(() => {
      const selectedRoom = screen.getByText('1 комната');
      expect(selectedRoom.closest('button')).toHaveClass('bg-accent/50');
    });
  });

  it('applies selected state styling to other option', async () => {
    const user = userEvent.setup();
    render(
      <RoomsFilter
        {...defaultProps}
        selectedOther={true}
      />
    );

    await user.click(screen.getByText('0+ комн.'));
    await waitFor(() => {
      const otherOption = screen.getByText('Другие (5+, студия)');
      expect(otherOption.closest('button')).toHaveClass('bg-accent/50');
    });
  });
});
