import { QueryClient } from '@tanstack/react-query';

const testQueryClients = new Set<QueryClient>();

export function createTestQueryClient() {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  testQueryClients.add(client);
  return client;
}

export function clearTestQueryClients() {
  for (const client of testQueryClients) {
    client.clear();
  }
  testQueryClients.clear();
}
