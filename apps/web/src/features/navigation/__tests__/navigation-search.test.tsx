import { beforeEach, expect, test } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { resetUIStore } from '@/test/reset-ui-store';
import { renderApp } from '@/test/render-app';

beforeEach(() => {
  resetUIStore();
});

test('renders operator workspace heading', async () => {
  renderApp();

  expect(await screen.findByText('Agent Control Plane')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Projects' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Inbox' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Settings' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Sessions' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Worktrees' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Diagnostics' })).not.toBeInTheDocument();
});

test('shows workspace search guidance when the operator types a query', async () => {
  renderApp();

  fireEvent.click(screen.getByRole('button', { name: /search/i }));
  const searchInput = await screen.findByPlaceholderText('Search workspace');
  fireEvent.change(searchInput, {
    target: { value: 'calc' },
  });

  await waitFor(() => {
    expect(screen.getByRole('option', { name: 'Open search results for “calc”' })).toBeInTheDocument();
  });

  expect(searchInput).toHaveValue('calc');
});

test('hydrates activity section from URL query params', async () => {
  renderApp({ route: '/?section=activity' });

  expect(await screen.findByText('Activity')).toBeInTheDocument();
});
