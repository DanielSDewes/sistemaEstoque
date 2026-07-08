import {
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
import {
  costCentersApi,
  customersApi,
  financeApi,
  financialCategoriesApi,
  suppliersApi,
} from '@/api/endpoints';
import type { FinancialDirection } from '@/api/types';
import { money } from '@/pages/finance/financeUtils';

interface Props {
  open: boolean;
  direction: FinancialDirection;
  onClose: () => void;
}

const today = () => new Date().toISOString().slice(0, 10);
const addDays = (iso: string, days: number) => {
  const d = new Date(iso);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
};

export default function AccountFormDialog({ open, direction, onClose }: Props) {
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const isReceivable = direction === 'receber';

  const [partyId, setPartyId] = useState<number | ''>('');
  const [document, setDocument] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [costCenterId, setCostCenterId] = useState<number | ''>('');
  const [issueDate, setIssueDate] = useState(today());
  const [total, setTotal] = useState('');
  const [count, setCount] = useState('1');
  const [firstDue, setFirstDue] = useState(addDays(today(), 30));
  const [interval, setInterval] = useState('30');

  const { data: customers } = useQuery({
    queryKey: ['customers', 'all'],
    queryFn: () => customersApi.list({ size: 200 }),
    enabled: open && isReceivable,
  });
  const { data: suppliers } = useQuery({
    queryKey: ['suppliers', 'all'],
    queryFn: () => suppliersApi.list({ size: 200 }),
    enabled: open && !isReceivable,
  });
  const { data: categories } = useQuery({
    queryKey: ['financial-categories', 'all'],
    queryFn: () => financialCategoriesApi.list({ size: 200 }),
    enabled: open,
  });
  const { data: costCenters } = useQuery({
    queryKey: ['cost-centers', 'all'],
    queryFn: () => costCentersApi.list({ size: 200 }),
    enabled: open,
  });

  useEffect(() => {
    if (open) {
      setPartyId('');
      setDocument('');
      setDescription('');
      setCategoryId('');
      setCostCenterId('');
      setIssueDate(today());
      setTotal('');
      setCount('1');
      setFirstDue(addDays(today(), 30));
      setInterval('30');
    }
  }, [open]);

  const totalNum = Number(total) || 0;
  const countNum = Math.max(Number(count) || 1, 1);
  const per = totalNum / countNum;

  const create = useMutation({
    mutationFn: () =>
      financeApi.createAccount({
        direction,
        customer_id: isReceivable ? Number(partyId) : null,
        supplier_id: isReceivable ? null : Number(partyId),
        document: document.trim() || null,
        description: description.trim() || null,
        category_id: categoryId === '' ? null : Number(categoryId),
        cost_center_id: costCenterId === '' ? null : Number(costCenterId),
        issue_date: issueDate,
        total_amount: totalNum,
        installment_plan: {
          count: countNum,
          first_due_date: firstDue,
          interval_days: Number(interval) || 0,
        },
      }),
    onSuccess: () => {
      enqueueSnackbar('Conta criada', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['finance-accounts'] });
      onClose();
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const partyOptions = isReceivable
    ? (customers?.items ?? []).map((c) => ({ id: c.id, label: `${c.name} — ${c.phone}` }))
    : (suppliers?.items ?? []).map((s) => ({ id: s.id, label: s.trade_name || s.legal_name }));

  const canSave = partyId !== '' && totalNum > 0;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Nova conta a {isReceivable ? 'receber' : 'pagar'}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField select label={isReceivable ? 'Cliente' : 'Fornecedor'} value={partyId} onChange={(e) => setPartyId(Number(e.target.value))}>
            {partyOptions.map((o) => <MenuItem key={o.id} value={o.id}>{o.label}</MenuItem>)}
          </TextField>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField label={isReceivable ? 'Documento (fatura)' : 'Nº da nota'} fullWidth value={document} onChange={(e) => setDocument(e.target.value)} />
            <TextField label="Emissão" type="date" value={issueDate} onChange={(e) => setIssueDate(e.target.value)} InputLabelProps={{ shrink: true }} />
          </Stack>
          <TextField label="Descrição" value={description} onChange={(e) => setDescription(e.target.value)} />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField select label="Categoria" fullWidth value={categoryId} onChange={(e) => setCategoryId(Number(e.target.value))}>
              <MenuItem value="">—</MenuItem>
              {categories?.items
                .filter((c) => c.kind === (isReceivable ? 'receita' : 'despesa'))
                .map((c) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
            </TextField>
            <TextField select label="Centro de custo" fullWidth value={costCenterId} onChange={(e) => setCostCenterId(Number(e.target.value))}>
              <MenuItem value="">—</MenuItem>
              {costCenters?.items.map((c) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
            </TextField>
          </Stack>

          <Typography variant="overline" color="text.secondary">Valor e parcelamento</Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField label="Valor total" type="number" value={total} onChange={(e) => setTotal(e.target.value)} inputProps={{ min: 0, step: '0.01' }} />
            <TextField label="Nº parcelas" type="number" value={count} onChange={(e) => setCount(e.target.value)} inputProps={{ min: 1, step: 1 }} sx={{ width: 120 }} />
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField label="1º vencimento" type="date" value={firstDue} onChange={(e) => setFirstDue(e.target.value)} InputLabelProps={{ shrink: true }} />
            <TextField label="Intervalo (dias)" type="number" value={interval} onChange={(e) => setInterval(e.target.value)} inputProps={{ min: 0, step: 1 }} sx={{ width: 160 }} />
          </Stack>
          {totalNum > 0 && (
            <Box sx={{ p: 1.5, bgcolor: 'action.hover', borderRadius: 2 }}>
              <Typography variant="body2">
                {countNum}x de aprox. <strong>{money(per)}</strong> (total {money(totalNum)})
              </Typography>
            </Box>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button variant="contained" disabled={!canSave || create.isPending} onClick={() => create.mutate()}>
          Salvar
        </Button>
      </DialogActions>
    </Dialog>
  );
}
