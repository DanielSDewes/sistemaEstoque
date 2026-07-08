import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useEffect, useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import { bankAccountsApi, financeApi, paymentMethodsApi } from '@/api/endpoints';
import type { FinancialAccount, FinancialDirection } from '@/api/types';
import { money } from '@/pages/finance/financeUtils';

interface Props {
  open: boolean;
  installmentId: number | null;
  balance: number;
  direction: FinancialDirection;
  onClose: () => void;
  onSettled: (account: FinancialAccount) => void;
}

const today = () => new Date().toISOString().slice(0, 10);

export default function SettlementDialog({ open, installmentId, balance, direction, onClose, onSettled }: Props) {
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [amount, setAmount] = useState('');
  const [settledAt, setSettledAt] = useState(today());
  const [paymentMethodId, setPaymentMethodId] = useState<number | ''>('');
  const [bankAccountId, setBankAccountId] = useState<number | ''>('');
  const [interest, setInterest] = useState('0');
  const [fine, setFine] = useState('0');
  const [discount, setDiscount] = useState('0');
  const [notes, setNotes] = useState('');

  const { data: methods } = useQuery({
    queryKey: ['payment-methods', 'all'],
    queryFn: () => paymentMethodsApi.list({ size: 200 }),
    enabled: open,
  });
  const { data: banks } = useQuery({
    queryKey: ['bank-accounts', 'all'],
    queryFn: () => bankAccountsApi.list({ size: 200 }),
    enabled: open,
  });
  const { data: suggested } = useQuery({
    queryKey: ['suggested-charges', installmentId],
    queryFn: () => financeApi.suggestedCharges(installmentId as number),
    enabled: open && installmentId != null,
  });

  useEffect(() => {
    if (open) {
      setAmount(String(balance));
      setSettledAt(today());
      setPaymentMethodId('');
      setBankAccountId('');
      setInterest('0');
      setFine('0');
      setDiscount('0');
      setNotes('');
    }
  }, [open, balance]);

  // Prefill interest/fine with the server suggestion for overdue installments.
  useEffect(() => {
    if (suggested && (suggested.interest > 0 || suggested.fine > 0)) {
      setInterest(String(suggested.interest));
      setFine(String(suggested.fine));
    }
  }, [suggested]);

  const num = (s: string) => Number(s) || 0;

  const settle = useMutation({
    mutationFn: () =>
      financeApi.settle(installmentId as number, {
        amount: num(amount),
        settled_at: settledAt || null,
        payment_method_id: paymentMethodId === '' ? null : Number(paymentMethodId),
        bank_account_id: bankAccountId === '' ? null : Number(bankAccountId),
        interest: num(interest),
        fine: num(fine),
        discount: num(discount),
        notes: notes.trim() || null,
      }),
    onSuccess: (account) => {
      enqueueSnackbar('Baixa registrada', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['finance-accounts'] });
      qc.invalidateQueries({ queryKey: ['bank-accounts'] });
      onSettled(account);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const remaining = balance + num(interest) + num(fine) - num(discount) - num(amount);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Registrar baixa ({direction === 'receber' ? 'recebimento' : 'pagamento'})</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Saldo da parcela: <strong>{money(balance)}</strong>
          </Typography>
          {suggested && suggested.days_overdue > 0 && (
            <Alert severity="warning" sx={{ py: 0 }}>
              {suggested.days_overdue} dia(s) em atraso — juros/multa sugeridos já preenchidos.
            </Alert>
          )}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField label="Valor" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} inputProps={{ min: 0, step: '0.01' }} autoFocus />
            <TextField label="Data" type="date" value={settledAt} onChange={(e) => setSettledAt(e.target.value)} InputLabelProps={{ shrink: true }} />
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField select label="Forma de pagamento" fullWidth value={paymentMethodId} onChange={(e) => setPaymentMethodId(Number(e.target.value))}>
              <MenuItem value="">—</MenuItem>
              {methods?.items.map((m) => <MenuItem key={m.id} value={m.id}>{m.name}</MenuItem>)}
            </TextField>
            <TextField select label="Conta bancária" fullWidth value={bankAccountId} onChange={(e) => setBankAccountId(Number(e.target.value))} helperText="Atualiza o saldo da conta">
              <MenuItem value="">—</MenuItem>
              {banks?.items.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
            </TextField>
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField label="Juros" type="number" value={interest} onChange={(e) => setInterest(e.target.value)} inputProps={{ min: 0, step: '0.01' }} />
            <TextField label="Multa" type="number" value={fine} onChange={(e) => setFine(e.target.value)} inputProps={{ min: 0, step: '0.01' }} />
            <TextField label="Desconto" type="number" value={discount} onChange={(e) => setDiscount(e.target.value)} inputProps={{ min: 0, step: '0.01' }} />
          </Stack>
          <TextField label="Observação" value={notes} onChange={(e) => setNotes(e.target.value)} />
          <Box sx={{ p: 1.5, bgcolor: 'action.hover', borderRadius: 2 }}>
            <Typography variant="body2">
              Saldo restante após a baixa: <strong>{money(Math.max(remaining, 0))}</strong>
            </Typography>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button variant="contained" disabled={num(amount) <= 0 || settle.isPending} onClick={() => settle.mutate()}>
          Confirmar baixa
        </Button>
      </DialogActions>
    </Dialog>
  );
}
