import { beforeEach, expect, test } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useUIStore } from '@/store/ui';
import { renderApp } from '@/test/render-app';

beforeEach(() => {
  useUIStore.getState().setSelectedProjectId('project-1');
  window.history.replaceState({}, '', '/');
});

test('renders activity timeline and filter controls', async () => {
  renderApp();

  fireEvent.click(await screen.findByRole('button', { name: 'Activity' }));

  await waitFor(() => {
    expect(screen.getByRole('heading', { name: 'Activity timeline' })).toBeInTheDocument();
  });

  expect(screen.getByRole('option', { name: 'All projects' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'All tasks' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'All sessions' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'All event types' })).toBeInTheDocument();
});
