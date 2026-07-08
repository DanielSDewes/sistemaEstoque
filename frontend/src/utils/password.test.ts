import { describe, expect, it } from 'vitest';

import { passwordSchema } from './password';

describe('passwordSchema', () => {
  it('accepts a strong password', () => {
    expect(passwordSchema.safeParse('Strong@123').success).toBe(true);
  });

  it.each([
    ['too short', 'A@1a'],
    ['no uppercase', 'weak@123'],
    ['no lowercase', 'WEAK@123'],
    ['no digit', 'Weak@abc'],
    ['no symbol', 'Weak1234'],
  ])('rejects %s', (_label, value) => {
    expect(passwordSchema.safeParse(value).success).toBe(false);
  });
});
