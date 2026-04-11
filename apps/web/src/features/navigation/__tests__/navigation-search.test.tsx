import { beforeEach, expect, test } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useUIStore } from '@/store/ui';
import { renderApp } from '@/test/render-app';

beforeEach(() => {
  useUIStore.getState().setSelectedProjectId(null);
  window.history.replaceState({}, '', '/');
});

test('renders operator workspace heading', async () => {
  renderApp();

  expect(await screen.findByRole('heading', { name: 'Local operator workspace' })).toBeInTheDocument();
});

test('shows workspace search guidance when the operator types a query', async () => {
  renderApp();

  const searchInput = screen.getByPlaceholderText('Search workspace');
  fireEvent.change(searchInput, {
    target: { value: 'calc' },
  });

  await waitFor(() => {
    expect(
      screen.getByText('Workspace-wide results across projects, tasks, questions, sessions, and events.'),
    ).toBeInTheDocument();
  });

  expect(searchInput).toHaveValue('calc');
  expect(screen.getByRole('heading', { name: 'Search Results' })).toBeInTheDocument();
});
