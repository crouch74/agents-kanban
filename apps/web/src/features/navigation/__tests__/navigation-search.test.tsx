import { beforeEach, expect, test } from 'vitest';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { resetUIStore } from '@/test/reset-ui-store';
import { renderApp } from '@/test/render-app';

beforeEach(() => {
  resetUIStore();
});

test('renders task board heading and simplified nav', async () => {
  renderApp();

  expect(await screen.findByText('Shared Task Board')).toBeInTheDocument();
  expect(screen.getAllByRole('button', { name: 'Projects' }).length).toBeGreaterThan(0);
  expect(screen.getAllByRole('button', { name: 'Search' }).length).toBeGreaterThan(0);
  expect(screen.getAllByRole('button', { name: 'Activity' }).length).toBeGreaterThan(0);
});

test('shows search results when operator types query', async () => {
  renderApp();

  fireEvent.click(screen.getAllByRole('button', { name: /search/i })[0]);
  const searchInput = await screen.findByPlaceholderText('Search workspace');
  fireEvent.change(searchInput, {
    target: { value: 'mock' },
  });

  await waitFor(() => {
    expect(screen.getByText('Mock task')).toBeInTheDocument();
  });
});
