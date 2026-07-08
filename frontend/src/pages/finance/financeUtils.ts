import type { FinancialDirection, FinancialStatus } from '@/api/types';

export const money = (n: number | null | undefined) =>
  n == null ? '—' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

type ChipColor = 'default' | 'success' | 'warning' | 'error' | 'info';

/** Label + color for a financial status, using direction to say pago vs recebido. */
export function statusInfo(
  status: FinancialStatus,
  direction: FinancialDirection,
): { label: string; color: ChipColor } {
  switch (status) {
    case 'quitado':
      return { label: direction === 'receber' ? 'Recebido' : 'Pago', color: 'success' };
    case 'parcial':
      return { label: 'Parcial', color: 'info' };
    case 'vencido':
      return { label: 'Vencido', color: 'error' };
    case 'cancelado':
      return { label: 'Cancelado', color: 'default' };
    case 'renegociado':
      return { label: 'Renegociado', color: 'warning' };
    default:
      return { label: 'Em aberto', color: 'warning' };
  }
}
