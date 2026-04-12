import '@testing-library/jest-dom';
import { afterEach } from 'vitest';
import { installApiMockServer } from './api-mock-server';
import { clearTestQueryClients } from './query-client';

installApiMockServer();

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// cmdk expects ResizeObserver in the test environment.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(globalThis as any).ResizeObserver = ResizeObserverMock;

afterEach(() => {
  clearTestQueryClients();
});
