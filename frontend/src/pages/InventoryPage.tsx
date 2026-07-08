import { zodResolver } from '@hookform/resolvers/zod';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
} from '@mui/material';
import { DataGrid, type GridColDef, type GridRowModel } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiErrorMessage } from '@/api/client';
import { inventoryApi } from '@/api/endpoints';
import type { Inventory, InventoryItem } from '@/api/types';
import PageHeader from '@/components/PageHeader';
import { useAuth } from '@/auth/AuthContext';

const STATUS_COLORS: Record<string, 'default' | 'info' | 'warning' | 'success' | 'error'> = {
  em_aberto: 'default',
  em_andamento: 'info',
  finalizado: 'warning',
  aprovado: 'success',
  cancelado: 'error',
};
const STATUS_LABELS: Record<string, string> = {
  em_aberto: 'Em aberto',
  em_andamento: 'Em andamento',
  finalizado: 'Finalizado',
  aprovado: 'Aprovado',
  cancelado: 'Cancelado',
};
const SCOPES = [
  { value: 'todo_estoque', label: 'Todo o estoque' },
  { value: 'categoria', label: 'Por categoria' },
  { value: 'grupo', label: 'Por grupo' },
  { value: 'corredor', label: 'Por corredor' },
  { value: 'prateleira', label: 'Por prateleira' },
];

const createSchema = z.object({
  code: z.string().min(1, 'Obrigatório'),
  scope: z.string().min(1),
  description: z.string().optional().or(z.literal('')),
});
type CreateData = z.infer<typeof createSchema>;

function InventoryDetailDialog({ id, onClose }: { id: number; onClose: () => void }) {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();

  const { data: inv } = useQuery({ queryKey: ['inventory', id], queryFn: () => inventoryApi.get(id) });
  const canApprove = hasPermission('inventory:approve');
  const editable = inv?.status === 'em_aberto' || inv?.status === 'em_andamento';

  const countMutation = useMutation({
    mutationFn: ({ itemId, qty }: { itemId: number; qty: number }) => inventoryApi.count(id, itemId, qty),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['inventory', id] }),
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const finishMutation = useMutation({
    mutationFn: () => inventoryApi.finish(id),
    onSuccess: () => {
      enqueueSnackbar('Inventário finalizado', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['inventory', id] });
      qc.invalidateQueries({ queryKey: ['inventories'] });
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const approveMutation = useMutation({
    mutationFn: () => inventoryApi.approve(id),
    onSuccess: () => {
      enqueueSnackbar('Inventário aprovado — ajustes gerados', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['inventory', id] });
      qc.invalidateQueries({ queryKey: ['inventories'] });
      qc.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const processRowUpdate = async (newRow: GridRowModel<InventoryItem>) => {
    if (newRow.counted_quantity != null) {
      await countMutation.mutateAsync({ itemId: newRow.id, qty: Number(newRow.counted_quantity) });
    }
    return newRow;
  };

  const columns: GridColDef<InventoryItem>[] = [
    { field: 'product_id', headerName: 'Produto', width: 90 },
    { field: 'system_quantity', headerName: 'Sistema', width: 110 },
    {
      field: 'counted_quantity',
      headerName: 'Contado',
      width: 130,
      editable,
      type: 'number',
    },
    {
      field: 'difference',
      headerName: 'Diferença',
      width: 120,
      renderCell: (p) => {
        const d = p.row.difference;
        if (d == null) return '—';
        return <Chip size="small" label={d} color={d === 0 ? 'default' : d > 0 ? 'success' : 'error'} />;
      },
    },
    {
      field: 'divergence_pct',
      headerName: 'Divergência %',
      width: 130,
      valueGetter: (v) => (v == null ? '—' : `${v}%`),
    },
  ];

  return (
    <Dialog open onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Inventário {inv?.code}{' '}
        {inv && <Chip size="small" sx={{ ml: 1 }} label={STATUS_LABELS[inv.status]} color={STATUS_COLORS[inv.status]} />}
      </DialogTitle>
      <DialogContent>
        {editable && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Edite a coluna <strong>Contado</strong> (duplo clique) para registrar a contagem física.
          </Alert>
        )}
        <Box sx={{ height: 420 }}>
          <DataGrid
            rows={inv?.items ?? []}
            columns={columns}
            processRowUpdate={processRowUpdate}
            onProcessRowUpdateError={(e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' })}
            disableColumnMenu
            disableRowSelectionOnClick
            hideFooter
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Fechar</Button>
        {editable && (
          <Button variant="outlined" onClick={() => finishMutation.mutate()} disabled={finishMutation.isPending}>
            Finalizar contagem
          </Button>
        )}
        {inv?.status === 'finalizado' && canApprove && (
          <Button variant="contained" color="success" onClick={() => approveMutation.mutate()} disabled={approveMutation.isPending}>
            Aprovar e gerar ajustes
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

export default function InventoryPage() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [detailId, setDetailId] = useState<number | null>(null);

  const canCreate = hasPermission('inventory:create');

  const { data, isFetching } = useQuery({ queryKey: ['inventories'], queryFn: () => inventoryApi.list({ size: 100 }) });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<CreateData>({
    resolver: zodResolver(createSchema),
    defaultValues: { code: '', scope: 'todo_estoque', description: '' },
  });

  const createMutation = useMutation({
    mutationFn: (values: CreateData) => inventoryApi.create(values),
    onSuccess: (inv) => {
      enqueueSnackbar('Inventário criado', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['inventories'] });
      setCreateOpen(false);
      reset();
      setDetailId(inv.id);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<Inventory>[] = [
    { field: 'code', headerName: 'Código', width: 140 },
    { field: 'description', headerName: 'Descrição', flex: 1, minWidth: 180 },
    { field: 'scope', headerName: 'Escopo', width: 150, valueGetter: (v) => SCOPES.find((s) => s.value === v)?.label ?? v },
    {
      field: 'status',
      headerName: 'Status',
      width: 150,
      renderCell: (p) => <Chip size="small" label={STATUS_LABELS[p.value as string]} color={STATUS_COLORS[p.value as string]} />,
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Inventário"
        subtitle="Contagem física com geração automática de ajustes após aprovação"
        actionLabel={canCreate ? 'Novo inventário' : undefined}
        onAction={canCreate ? () => setCreateOpen(true) : undefined}
      />
      <Box sx={{ height: 560 }}>
        <DataGrid
          rows={data ?? []}
          columns={columns}
          loading={isFetching}
          onRowClick={(p) => setDetailId(p.row.id)}
          disableColumnMenu
          disableRowSelectionOnClick
          sx={{ bgcolor: 'background.paper', '& .MuiDataGrid-row': { cursor: 'pointer' } }}
        />
      </Box>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="xs" fullWidth>
        <form onSubmit={handleSubmit((v) => createMutation.mutate(v))}>
          <DialogTitle>Novo inventário</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField label="Código" {...register('code')} error={!!errors.code} helperText={errors.code?.message} />
              <TextField select label="Escopo" defaultValue="todo_estoque" {...register('scope')}>
                {SCOPES.map((s) => (
                  <MenuItem key={s.value} value={s.value}>
                    {s.label}
                  </MenuItem>
                ))}
              </TextField>
              <TextField label="Descrição" {...register('description')} />
              <Alert severity="info">
                Para escopos específicos (categoria, corredor, etc.), o inventário incluirá todos os produtos ativos do escopo.
              </Alert>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateOpen(false)}>Cancelar</Button>
            <Button type="submit" variant="contained" disabled={createMutation.isPending}>
              Criar
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {detailId && <InventoryDetailDialog id={detailId} onClose={() => setDetailId(null)} />}
    </Box>
  );
}
