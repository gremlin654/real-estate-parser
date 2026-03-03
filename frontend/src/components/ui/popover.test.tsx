import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Popover, PopoverTrigger, PopoverContent } from './popover';

describe('Popover', () => {
  it('renders PopoverTrigger', () => {
    render(
      <Popover>
        <PopoverTrigger>Open Popover</PopoverTrigger>
        <PopoverContent>Popover Content</PopoverContent>
      </Popover>
    );

    expect(screen.getByText('Open Popover')).toBeInTheDocument();
  });

  it('opens popover when trigger is clicked', async () => {
    render(
      <Popover>
        <PopoverTrigger>Open Popover</PopoverTrigger>
        <PopoverContent>Popover Content</PopoverContent>
      </Popover>
    );

    const trigger = screen.getByText('Open Popover');
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Popover Content')).toBeInTheDocument();
    });
  });

  it('closes popover when trigger is clicked again', async () => {
    render(
      <Popover>
        <PopoverTrigger>Open Popover</PopoverTrigger>
        <PopoverContent>Popover Content</PopoverContent>
      </Popover>
    );

    const trigger = screen.getByText('Open Popover');
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Popover Content')).toBeInTheDocument();
    });

    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.queryByText('Popover Content')).not.toBeInTheDocument();
    });
  });

  it('renders PopoverContent with children', async () => {
    render(
      <Popover>
        <PopoverTrigger>Open</PopoverTrigger>
        <PopoverContent>
          <div>
            <h3>Title</h3>
            <p>Content</p>
          </div>
        </PopoverContent>
      </Popover>
    );

    const trigger = screen.getByText('Open');
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });
  });

  it('applies custom className to PopoverContent', async () => {
    render(
      <Popover>
        <PopoverTrigger>Open</PopoverTrigger>
        <PopoverContent className="custom-popover">Content</PopoverContent>
      </Popover>
    );

    const trigger = screen.getByText('Open');
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Content')).toBeInTheDocument();
    });
  });

  it('renders Popover with align prop', async () => {
    render(
      <Popover>
        <PopoverTrigger>Open</PopoverTrigger>
        <PopoverContent align="start">Aligned Content</PopoverContent>
      </Popover>
    );

    const trigger = screen.getByText('Open');
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Aligned Content')).toBeInTheDocument();
    });
  });

  it('renders Popover with sideOffset prop', async () => {
    render(
      <Popover>
        <PopoverTrigger>Open</PopoverTrigger>
        <PopoverContent sideOffset={10}>Offset Content</PopoverContent>
      </Popover>
    );

    const trigger = screen.getByText('Open');
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Offset Content')).toBeInTheDocument();
    });
  });

  it('renders complex content in Popover', async () => {
    render(
      <Popover>
        <PopoverTrigger>Open Menu</PopoverTrigger>
        <PopoverContent>
          <div className="space-y-2">
            <button>Option 1</button>
            <button>Option 2</button>
            <button>Option 3</button>
          </div>
        </PopoverContent>
      </Popover>
    );

    const trigger = screen.getByText('Open Menu');
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Option 1')).toBeInTheDocument();
      expect(screen.getByText('Option 2')).toBeInTheDocument();
      expect(screen.getByText('Option 3')).toBeInTheDocument();
    });
  });
});
