import PaymentsIcon from '@mui/icons-material/Payments';
import UndoIcon from '@mui/icons-material/Undo';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import { financeApi } from '@/api/endpoints';
import type { FinancialInstallment } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import { money, statusInfo } from '@/pages/finance/financeUtils';
import SettlementDialog from '@/pages/finance/SettlementDialog';

interface Props {
  open: boolean;
  accountId: number | null;
  onClose: () => void;
}

export default function AccountDetailDialog({ open, accountId, onClose }: Props) {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [settleTarget, setSettleTarget] = useState<FinancialInstallment | null>(null);

  const canSettle = hasPermission('finance:settle');
  const canCancel = hasPermission('finance:cancel');

  const { data: account } = useQuery({
    queryKey: ['finance-account', accountId],
    queryFn: () => financeApi.getAccount(accountId as number),
    enabled: open && accountId != null,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['finance-account', accountId] });
    qc.invalidateQueries({ queryKey: ['finance-accounts'] });
  };
  const onError = (e: unknown) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' });

  const cancelSettlement = useMutation({
    mutationFn: (id: number) => financeApi.cancelSettlement(id),
    onSuccess: () => { enqueueSnackbar('Baixa estornada', { variant: 'success' }); invalidate(); },
    onError,
  });
  const cancelAccount = useMutation({
    mutationFn: () => financeApi.cancelAccount(accountId as number),
    onSuccess: () => { enqueueSnackbar('Conta cancelada', { variant: 'success' }); invalidate(); onClose(); },
    onError,
  });

  if (!account) return null;
  const dir = account.direction;
  const st = statusInfo(account.status, dir);
  const settlements = account.installments.flatMap((i) =>
    i.settlements.filter((s) => !s.is_cancelled).map((s) => ({ ...s, installmentNumber: i.number })),
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap">
          <Typography variant="h6">
            {account.document || `Conta #${account.id}`}
          </Typography>
          <Chip size="small" color={st.color} label={st.label} />
          <Box sx={{ flex: 1 }} />
          {canCancel && account.status !== 'cancelado' && account.status !== 'quitado' && (
            <Button size="small" color="error" onClick={() => cancelAccount.mutate()} disabled={cancelAccount.isPending}>
              Cancelar conta
            </Button>
          )}
        </Stack>
        <Typography variant="caption" color="text.secondary">
          {dir === 'receber' ? 'Cliente' : 'Fornecedor'}: {account.party_name ?? '—'}
          {account.category_name && ` · ${account.category_name}`}
          {account.description && ` · ${account.description}`}
        </Typography>
      </DialogTitle>
      <DialogContent dividers>
        <Stack direction="row" spacing={3} sx={{ mb: 2 }} flexWrap="wrap">
          <Box><Typography variant="caption" color="text.secondary">Total</Typography><Typography>{money(account.total_amount)}</Typography></Box>
          <Box><Typography variant="caption" color="text.secondary">Baixado</Typography><Typography>{money(account.total_paid)}</Typography></Box>
          <Box><Typography variant="caption" color="text.secondary">Saldo</Typography><Typography fontWeight={700}>{money(account.balance)}</Typography></Box>
        </Stack>

        <Typography variant="subtitle2" gutterBottom>Parcelas</Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Parcela</TableCell>
              <TableCell>Vencimento</TableCell>
              <TableCell align="right">Valor</TableCell>
              <TableCell align="right">Saldo</TableCell>
              <TableCell>Status</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {account.installments.map((i) => {
              const is = statusInfo(i.status, dir);
              const settleable = canSettle && (i.status === 'em_aberto' || i.status === 'parcial' || i.status === 'vencido');
              return (
                <TableRow key={i.id}>
                  <TableCell>{i.number}/{i.total_installments}</TableCell>
                  <TableCell>{new Date(i.due_date).toLocaleDateString('pt-BR')}</TableCell>
                  <TableCell align="right">{money(i.original_amount)}</TableCell>
                  <TableCell align="right">{money(i.balance)}</TableCell>
                  <TableCell><Chip size="small" color={is.color} label={is.label} /></TableCell>
                  <TableCell align="right">
                    {settleable && (
                      <Tooltip title="Baixar">
                        <IconButton size="small" color="primary" onClick={() => setSettleTarget(i)}>
                          <PaymentsIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>

        {settlements.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>Baixas</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Parcela</TableCell>
                  <TableCell>Data</TableCell>
                  <TableCell align="right">Valor</TableCell>
                  <TableCell>Forma</TableCell>
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {settlements.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell>{s.installmentNumber}</TableCell>
                    <TableCell>{new Date(s.settled_at).toLocaleDateString('pt-BR')}</TableCell>
                    <TableCell align="right">{money(s.amount)}</TableCell>
                    <TableCell>{s.payment_method_name ?? '—'}</TableCell>
                    <TableCell align="right">
                      {canSettle && (
                        <Tooltip title="Estornar baixa">
                          <IconButton size="small" color="error" onClick={() => cancelSettlement.mutate(s.id)}>
                            <UndoIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}
      </DialogContent>

      <SettlementDialog
        open={!!settleTarget}
        installmentId={settleTarget?.id ?? null}
        balance={settleTarget?.balance ?? 0}
        direction={dir}
        onClose={() => setSettleTarget(null)}
        onSettled={() => { setSettleTarget(null); invalidate(); }}
      />
    </Dialog>
  );
}
