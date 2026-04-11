import '@testing-library/jest-dom';
import { afterEach } from 'vitest';
import { installApiMockServer } from './api-mock-server';
import { clearTestQueryClients } from './query-client';

installApiMockServer();

afterEach(() => {
  clearTestQueryClients();
});
