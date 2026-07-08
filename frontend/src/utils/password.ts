import { z } from 'zod';

/** Mirrors the backend password policy (length + character classes). */
export const passwordSchema = z
  .string()
  .min(8, 'Mínimo de 8 caracteres')
  .regex(/[A-Z]/, 'Inclua uma letra maiúscula')
  .regex(/[a-z]/, 'Inclua uma letra minúscula')
  .regex(/\d/, 'Inclua um número')
  .regex(/[^A-Za-z0-9]/, 'Inclua um símbolo');
