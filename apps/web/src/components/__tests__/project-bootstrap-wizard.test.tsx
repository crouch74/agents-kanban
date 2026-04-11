import { beforeEach, expect, test } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useUIStore } from '@/store/ui';
import { renderApp } from '@/test/render-app';

beforeEach(() => {
  useUIStore.getState().setSelectedProjectId(null);
  window.history.replaceState({}, '', '/');
});

test('submits the project bootstrap wizard and shows kickoff summary details', async () => {
  renderApp();

  fireEvent.change(screen.getByPlaceholderText('Acme migration program'), {
    target: { value: 'Bootstrap Demo' },
  });
  fireEvent.change(screen.getByPlaceholderText('/absolute/path/to/repo'), {
    target: { value: '/tmp/demo-repo' },
  });
  fireEvent.change(
    screen.getByPlaceholderText(
      'Describe the work to kick off. ACP will ask the agent to clarify requirements and create tasks/subtasks.',
    ),
    {
      target: { value: 'Plan the initial implementation and create tasks.' },
    },
  );

  fireEvent.click(screen.getByRole('button', { name: /launch bootstrap/i }));

  await waitFor(() => {
    expect(screen.getByText('Bootstrap Demo is ready')).toBeInTheDocument();
  });
  expect(screen.getByText('Kickoff task: Kick off planning and board setup')).toBeInTheDocument();
  expect(screen.getByText('/tmp/demo-repo')).toBeInTheDocument();
  expect(screen.getByText('acp-project-1')).toBeInTheDocument();
});

test('quick create keeps new task disabled until a project is selected', async () => {
  renderApp();

  fireEvent.click(await screen.findByRole('button', { name: 'Quick create' }));

  expect(screen.getByRole('button', { name: 'New project bootstrap' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'New task' })).toBeDisabled();
  expect(screen.getByText('Select a project first to create a task.')).toBeInTheDocument();
});
