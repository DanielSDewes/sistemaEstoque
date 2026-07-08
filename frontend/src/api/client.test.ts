import { describe, expect, it } from 'vitest';

import { apiErrorMessage } from './client';

describe('apiErrorMessage', () => {
  it('extracts the API detail from an axios-like error', () => {
    const error = {
      isAxiosError: true,
      response: { data: { detail: 'Saldo insuficiente' } },
      message: 'Request failed',
    };
    expect(apiErrorMessage(error)).toBe('Saldo insuficiente');
  });

  it('falls back to the provided message for unknown errors', () => {
    expect(apiErrorMessage(new Error('x'), 'fallback')).toBe('fallback');
  });
});
