import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from './dialog';

describe('Dialog', () => {
  it('renders DialogTrigger', () => {
    render(
      <Dialog>
        <DialogTrigger>Open Dialog</DialogTrigger>
        <DialogContent>
          <DialogTitle>Dialog Title</DialogTitle>
          <DialogDescription>Description</DialogDescription>
        </DialogContent>
      </Dialog>
    );

    expect(screen.getByText('Open Dialog')).toBeInTheDocument();
  });

  it('opens dialog when trigger is clicked', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open Dialog</DialogTrigger>
        <DialogContent>
          <DialogTitle>Dialog Title</DialogTitle>
          <DialogDescription>Dialog Description</DialogDescription>
        </DialogContent>
      </Dialog>
    );

    const trigger = screen.getByText('Open Dialog');
    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Dialog Title')).toBeInTheDocument();
    });
  });

  it('renders DialogHeader', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Header Title</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );

    fireEvent.click(screen.getByText('Open'));

    await waitFor(() => {
      expect(screen.getByText('Header Title')).toBeInTheDocument();
    });
  });

  it('renders DialogFooter', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogFooter>
            <button>Footer Button</button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );

    fireEvent.click(screen.getByText('Open'));

    await waitFor(() => {
      expect(screen.getByText('Footer Button')).toBeInTheDocument();
    });
  });

  it('renders Dialog with custom className', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent className="custom-dialog">
          <DialogTitle>Dialog</DialogTitle>
        </DialogContent>
      </Dialog>
    );

    fireEvent.click(screen.getByText('Open'));

    await waitFor(() => {
      expect(screen.getByText('Dialog')).toBeInTheDocument();
    });
  });

  it('renders DialogTitle with custom className', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle className="custom-title">Custom Title</DialogTitle>
        </DialogContent>
      </Dialog>
    );

    fireEvent.click(screen.getByText('Open'));

    await waitFor(() => {
      expect(screen.getByText('Custom Title')).toBeInTheDocument();
    });
  });

  it('renders DialogDescription with custom className', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Title</DialogTitle>
          <DialogDescription className="custom-desc">Description</DialogDescription>
        </DialogContent>
      </Dialog>
    );

    fireEvent.click(screen.getByText('Open'));

    await waitFor(() => {
      expect(screen.getByText('Description')).toBeInTheDocument();
    });
  });

  it('does not close when clicking content', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open Dialog</DialogTrigger>
        <DialogContent>
          <DialogTitle>Dialog Title</DialogTitle>
          <div data-testid="content">Content</div>
        </DialogContent>
      </Dialog>
    );

    fireEvent.click(screen.getByText('Open Dialog'));

    await waitFor(() => {
      expect(screen.getByText('Dialog Title')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('content'));

    expect(screen.getByText('Dialog Title')).toBeInTheDocument();
  });
});
