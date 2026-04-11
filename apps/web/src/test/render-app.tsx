import { QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import { App } from '@/App';
import { createTestQueryClient } from '@/test/query-client';

type RenderAppOptions = {
  route?: string;
};

export function renderApp(options: RenderAppOptions = {}) {
  const { route = '/' } = options;
  window.history.replaceState({}, '', route);

  const queryClient = createTestQueryClient();

  return {
    queryClient,
    ...render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>,
    ),
  };
}
