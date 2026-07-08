import EditIcon from '@mui/icons-material/Edit';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Stack,
  TextField,
} from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useEffect, useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import { bankAccountsApi } from '@/api/endpoints';
import type { BankAccount, Status } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import PageHeader from '@/components/PageHeader';

const money = (n: number) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

interface FormState {
  name: string;
  bank: string;
  agency: string;
  account_number: string;
  opening_balance: string;
  status: Status;
}

const EMPTY: FormState = {
  name: '', bank: '', agency: '', account_number: '', opening_balance: '0', status: 'ativo',
};

export default function BankAccountsPage() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<BankAccount | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY);

  const canEdit = hasPermission('finance:create') || hasPermission('finance:update');

  const { data, isFetching } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankAccountsApi.list({ size: 200 }),
  });

  useEffect(() => {
    if (open) {
      setForm(
        editing
          ? {
              name: editing.name,
              bank: editing.bank ?? '',
              agency: editing.agency ?? '',
              account_number: editing.account_number ?? '',
              opening_balance: String(editing.opening_balance),
              status: editing.status,
            }
          : EMPTY,
      );
    }
  }, [open, editing]);

  const set = (k: keyof FormState, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const save = useMutation({
    mutationFn: () => {
      const payload = {
        name: form.name,
        bank: form.bank || null,
        agency: form.agency || null,
        account_number: form.account_number || null,
        status: form.status,
        ...(editing ? {} : { opening_balance: Number(form.opening_balance) || 0 }),
      };
      return editing ? bankAccountsApi.update(editing.id, payload) : bankAccountsApi.create(payload);
    },
    onSuccess: () => {
      enqueueSnackbar('Conta bancária salva', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['bank-accounts'] });
      setOpen(false);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<BankAccount>[] = [
    { field: 'name', headerName: 'Conta', flex: 1, minWidth: 160 },
    { field: 'bank', headerName: 'Banco', width: 140 },
    { field: 'agency', headerName: 'Agência', width: 100 },
    { field: 'account_number', headerName: 'Número', width: 120 },
    {
      field: 'current_balance',
      headerName: 'Saldo atual',
      width: 140,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (v) => money(v as number),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 110,
      renderCell: (p) => (
        <Chip size="small" label={p.value === 'ativo' ? 'Ativo' : 'Inativo'} color={p.value === 'ativo' ? 'success' : 'default'} />
      ),
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 80,
      sortable: false,
      renderCell: (p) =>
        canEdit ? (
          <IconButton size="small" onClick={() => { setEditing(p.row); setOpen(true); }}>
            <EditIcon fontSize="small" />
          </IconButton>
        ) : null,
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Contas Bancárias"
        subtitle="Caixa e bancos — o saldo é atualizado pelas baixas"
        actionLabel={canEdit ? 'Nova conta' : undefined}
        onAction={canEdit ? () => { setEditing(null); setOpen(true); } : undefined}
      />
      <Box sx={{ height: 560 }}>
        <DataGrid
          rows={data?.items ?? []}
          columns={columns}
          loading={isFetching}
          pageSizeOptions={[10, 20, 50]}
          initialState={{ pagination: { paginationModel: { pageSize: 20 } } }}
          disableColumnMenu
          disableRowSelectionOnClick
          sx={{ bgcolor: 'background.paper' }}
        />
      </Box>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editing ? 'Editar' : 'Nova'} conta bancária</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Nome (ex.: Caixa, Banco X)" value={form.name} onChange={(e) => set('name', e.target.value)} autoFocus />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField label="Banco" fullWidth value={form.bank} onChange={(e) => set('bank', e.target.value)} />
              <TextField label="Agência" value={form.agency} onChange={(e) => set('agency', e.target.value)} sx={{ width: 140 }} />
              <TextField label="Conta" value={form.account_number} onChange={(e) => set('account_number', e.target.value)} sx={{ width: 160 }} />
            </Stack>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Saldo inicial" type="number" value={form.opening_balance}
                onChange={(e) => set('opening_balance', e.target.value)}
                disabled={!!editing}
                helperText={editing ? 'O saldo é gerido pelas movimentações' : undefined}
                sx={{ width: 200 }}
              />
              <TextField select label="Status" value={form.status} onChange={(e) => set('status', e.target.value)} sx={{ width: 160 }}>
                <MenuItem value="ativo">Ativo</MenuItem>
                <MenuItem value="inativo">Inativo</MenuItem>
              </TextField>
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancelar</Button>
          <Button variant="contained" disabled={!form.name.trim() || save.isPending} onClick={() => save.mutate()}>
            Salvar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
