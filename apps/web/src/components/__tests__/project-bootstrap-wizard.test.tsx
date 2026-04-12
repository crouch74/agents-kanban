import { beforeEach, expect, test } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { resetUIStore } from '@/test/reset-ui-store';
import { renderApp } from '@/test/render-app';

beforeEach(() => {
  resetUIStore();
});

test('submits the project bootstrap wizard and shows kickoff summary details', async () => {
  renderApp({ route: '/?section=projects&project=project-1' });

  fireEvent.click(await screen.findByRole('button', { name: /\+ new project/i }));

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

test('opens project bootstrap in a dialog from the project switcher', async () => {
  renderApp({ route: '/?section=projects&project=project-1' });

  fireEvent.click(await screen.findByRole('button', { name: /\+ new project/i }));

  expect(await screen.findByText('New Project')).toBeInTheDocument();
  expect(screen.getByPlaceholderText('Acme migration program')).toBeInTheDocument();
});
