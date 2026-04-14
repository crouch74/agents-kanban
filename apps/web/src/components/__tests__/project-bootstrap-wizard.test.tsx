import { expect, test, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ProjectBootstrapWizard } from '@/components/project-bootstrap-wizard';

test('submits simplified project creation payload', async () => {
  const onCreate = vi.fn().mockResolvedValue(undefined);

  render(
    <ProjectBootstrapWizard
      isPending={false}
      onCreate={onCreate}
    />,
  );

  fireEvent.change(screen.getByPlaceholderText('Acme migration program'), {
    target: { value: 'Shared Board' },
  });
  fireEvent.change(screen.getByPlaceholderText('Optional project description'), {
    target: { value: 'Task coordination' },
  });

  fireEvent.click(screen.getByRole('button', { name: /create project/i }));

  await waitFor(() => {
    expect(onCreate).toHaveBeenCalledWith({ name: 'Shared Board', description: 'Task coordination' });
  });
});
