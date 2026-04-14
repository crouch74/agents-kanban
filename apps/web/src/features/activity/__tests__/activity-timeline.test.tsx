import { beforeEach, expect, test } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useUIStore } from '@/store/ui';
import { resetUIStore } from '@/test/reset-ui-store';
import { renderApp } from '@/test/render-app';

beforeEach(() => {
  resetUIStore();
  useUIStore.getState().setSelectedProjectId('project-1');
});

test('renders simplified activity timeline', async () => {
  renderApp({ route: '/activity' });
  fireEvent.click(screen.getAllByRole('button', { name: 'Activity' })[0]);

  await waitFor(() => {
    expect(screen.getByRole('heading', { name: 'Activity' })).toBeInTheDocument();
  });

  expect(screen.getByText('Shared Task Board')).toBeInTheDocument();
});
