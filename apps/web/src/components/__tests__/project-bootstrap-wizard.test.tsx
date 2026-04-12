import { beforeEach, expect, test, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ProjectBootstrapWizard } from '@/components/project-bootstrap-wizard';
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

  fireEvent.click(screen.getByRole('button', { name: /review bootstrap/i }));

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

test('renders a scrollable preview region when confirmation is required', async () => {
  const onPreview = vi.fn().mockResolvedValue({
    repo_path: '/tmp/demo-repo',
    stack_preset: 'nextjs',
    stack_notes: null,
    use_worktree: false,
    repo_initialized_on_confirm: false,
    scaffold_applied_on_confirm: false,
    has_existing_commits: true,
    confirmation_required: true,
    execution_path: '/tmp/demo-repo',
    execution_branch: 'main',
    planned_changes: Array.from({ length: 8 }, (_, index) => ({
      path: `.acp/file-${index}.md`,
      action: 'create_or_update' as const,
      description: `Planned change ${index}`,
    })),
  });

  render(
    <ProjectBootstrapWizard
      isPreviewPending={false}
      isConfirmPending={false}
      onPreview={onPreview}
      onConfirm={vi.fn().mockResolvedValue({}) as never}
    />,
  );

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

  fireEvent.click(screen.getByRole('button', { name: /review bootstrap/i }));

  const scrollRegion = await screen.findByTestId('bootstrap-preview-scroll-region');
  expect(scrollRegion.className).toContain('max-h-64');
  expect(scrollRegion.className).toContain('overflow-y-auto');
});
