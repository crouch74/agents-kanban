import { beforeEach, expect, test } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useUIStore } from '@/store/ui';
import { resetUIStore } from '@/test/reset-ui-store';
import { renderApp } from '@/test/render-app';

beforeEach(() => {
  resetUIStore();
  useUIStore.getState().setSelectedProjectId('project-1');
});

test('renders activity timeline and filter controls', async () => {
  renderApp({ route: '/?section=activity&project=project-1' });

  await waitFor(() => {
    expect(screen.getByRole('heading', { name: 'Activity timeline' })).toBeInTheDocument();
  });

  expect(screen.getByRole('option', { name: 'All projects' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'All tasks' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'All sessions' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'All event types' })).toBeInTheDocument();
});
