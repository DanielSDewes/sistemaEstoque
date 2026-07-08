import CancelIcon from '@mui/icons-material/Cancel';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import VisibilityIcon from '@mui/icons-material/Visibility';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import { ordersApi } from '@/api/endpoints';
import type { Order, OrderStatus } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import ConfirmDialog from '@/components/ConfirmDialog';
import PageHeader from '@/components/PageHeader';
import SearchBar from '@/components/SearchBar';
import OrderFormDialog from '@/pages/orders/OrderFormDialog';

const money = (n: number | null | undefined) =>
  n == null ? '—' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const STATUS_LABEL: Record<OrderStatus, { label: string; color: 'default' | 'success' | 'error' }> = {
  rascunho: { label: 'Rascunho', color: 'default' },
  confirmado: { label: 'Confirmado', color: 'success' },
  cancelado: { label: 'Cancelado', color: 'error' },
};

function OrderDetailDialog({ order, onClose }: { order: Order | null; onClose: () => void }) {
  if (!order) return null;
  return (
    <Dialog open={!!order} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Pedido {order.number}
        <Chip
          size="small"
          sx={{ ml: 1 }}
          color={STATUS_LABEL[order.status].color}
          label={STATUS_LABEL[order.status].label}
        />
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Cliente: {order.customer.name} · {new Date(order.order_date).toLocaleDateString('pt-BR')}
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Produto</TableCell>
              <TableCell align="right">Qtd</TableCell>
              <TableCell align="right">Preço unit.</TableCell>
              <TableCell align="right">Subtotal</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {order.items.map((it) => (
              <TableRow key={it.id}>
                <TableCell>{it.product_name}</TableCell>
                <TableCell align="right">{it.quantity}</TableCell>
                <TableCell align="right">{money(it.unit_price)}</TableCell>
                <TableCell align="right">{money(it.line_total)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <Box sx={{ mt: 2, ml: 'auto', maxWidth: 320 }}>
          <Stack direction="row" justifyContent="space-between"><Typography variant="body2" color="text.secondary">Receita</Typography><Typography variant="body2">{money(order.total_amount)}</Typography></Stack>
          <Stack direction="row" justifyContent="space-between"><Typography variant="body2" color="text.secondary">Custo dos produtos</Typography><Typography variant="body2">{money(order.total_cost)}</Typography></Stack>
          <Stack direction="row" justifyContent="space-between"><Typography variant="body2" color="text.secondary">Custo extra</Typography><Typography variant="body2">{money(order.extra_cost)}</Typography></Stack>
          <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.5 }}>
            <Typography variant="subtitle1" fontWeight={700}>Lucro</Typography>
            <Typography variant="subtitle1" fontWeight={700} color={order.profit >= 0 ? 'success.main' : 'error.main'}>
              {money(order.profit)}
            </Typography>
          </Stack>
        </Box>
        {order.notes && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Obs.: {order.notes}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Fechar</Button>
      </DialogActions>
    </Dialog>
  );
}

export default function OrdersPage() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<OrderStatus | ''>('');
  const [formOpen, setFormOpen] = useState(false);
  const [detail, setDetail] = useState<Order | null>(null);
  const [confirmTarget, setConfirmTarget] = useState<Order | null>(null);
  const [cancelTarget, setCancelTarget] = useState<Order | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const canCreate = hasPermission('order:create');
  const canConfirm = hasPermission('order:confirm');
  const canCancel = hasPermission('order:cancel');

  const { data, isFetching } = useQuery({
    queryKey: ['orders', page, pageSize, search, status],
    queryFn: () =>
      ordersApi.list({
        page: page + 1,
        size: pageSize,
        q: search,
        status: status || undefined,
      }),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['orders'] });
  const onError = (e: unknown) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' });

  const confirmMutation = useMutation({
    mutationFn: (id: number) => ordersApi.confirm(id),
    onSuccess: () => {
      enqueueSnackbar('Pedido confirmado, estoque baixado', { variant: 'success' });
      invalidate();
      setConfirmTarget(null);
    },
    onError,
  });

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => ordersApi.cancel(id, reason),
    onSuccess: () => {
      enqueueSnackbar('Pedido cancelado', { variant: 'success' });
      invalidate();
      setCancelTarget(null);
      setCancelReason('');
    },
    onError,
  });

  const columns: GridColDef<Order>[] = [
    { field: 'number', headerName: 'Pedido', width: 130 },
    {
      field: 'customer',
      headerName: 'Cliente',
      flex: 1,
      minWidth: 180,
      valueGetter: (_v, row) => row.customer?.name,
    },
    {
      field: 'order_date',
      headerName: 'Data',
      width: 120,
      valueGetter: (v) => new Date(v as string).toLocaleDateString('pt-BR'),
    },
    {
      field: 'items',
      headerName: 'Itens',
      width: 80,
      valueGetter: (_v, row) => row.items.length,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 130,
      renderCell: (p) => (
        <Chip size="small" color={STATUS_LABEL[p.value as OrderStatus].color} label={STATUS_LABEL[p.value as OrderStatus].label} />
      ),
    },
    {
      field: 'total_amount',
      headerName: 'Total',
      width: 130,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (v) => money(v as number),
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 140,
      sortable: false,
      renderCell: (p) => (
        <>
          <IconButton size="small" onClick={() => setDetail(p.row)} title="Detalhes">
            <VisibilityIcon fontSize="small" />
          </IconButton>
          {canConfirm && p.row.status === 'rascunho' && (
            <IconButton size="small" color="success" onClick={() => setConfirmTarget(p.row)} title="Confirmar (baixa estoque)">
              <CheckCircleIcon fontSize="small" />
            </IconButton>
          )}
          {canCancel && p.row.status !== 'cancelado' && (
            <IconButton size="small" color="error" onClick={() => setCancelTarget(p.row)} title="Cancelar">
              <CancelIcon fontSize="small" />
            </IconButton>
          )}
        </>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Pedidos"
        subtitle="Pedidos de venda vinculados a clientes"
        actionLabel={canCreate ? 'Novo pedido' : undefined}
        onAction={canCreate ? () => setFormOpen(true) : undefined}
      />
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <SearchBar placeholder="Buscar por número ou cliente..." onSearch={(v) => { setPage(0); setSearch(v); }} />
        <TextField
          select size="small" label="Status" value={status}
          onChange={(e) => { setPage(0); setStatus(e.target.value as OrderStatus | ''); }}
          sx={{ minWidth: 180, bgcolor: 'background.paper' }}
        >
          <MenuItem value="">Todos</MenuItem>
          <MenuItem value="rascunho">Rascunho</MenuItem>
          <MenuItem value="confirmado">Confirmado</MenuItem>
          <MenuItem value="cancelado">Cancelado</MenuItem>
        </TextField>
      </Stack>
      <Box sx={{ height: 560, mt: 2 }}>
        <DataGrid
          rows={data?.items ?? []}
          columns={columns}
          loading={isFetching}
          rowCount={data?.total ?? 0}
          paginationMode="server"
          paginationModel={{ page, pageSize }}
          onPaginationModelChange={(m) => { setPage(m.page); setPageSize(m.pageSize); }}
          pageSizeOptions={[10, 20, 50]}
          disableColumnMenu
          disableRowSelectionOnClick
          sx={{ bgcolor: 'background.paper' }}
        />
      </Box>

      <OrderFormDialog open={formOpen} onClose={() => setFormOpen(false)} />
      <OrderDetailDialog order={detail} onClose={() => setDetail(null)} />

      <ConfirmDialog
        open={!!confirmTarget}
        title="Confirmar pedido"
        message={`Confirmar o pedido ${confirmTarget?.number}? Isto dará baixa no estoque dos itens.`}
        confirmLabel="Confirmar"
        loading={confirmMutation.isPending}
        onClose={() => setConfirmTarget(null)}
        onConfirm={() => confirmTarget && confirmMutation.mutate(confirmTarget.id)}
      />

      <Dialog open={!!cancelTarget} onClose={() => setCancelTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Cancelar pedido {cancelTarget?.number}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {cancelTarget?.status === 'confirmado'
              ? 'O estoque baixado será estornado.'
              : 'O pedido em rascunho será cancelado.'}
          </Typography>
          <TextField
            autoFocus fullWidth label="Motivo" value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            error={cancelReason.length > 0 && cancelReason.trim().length < 3}
            helperText="Mínimo de 3 caracteres"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelTarget(null)}>Voltar</Button>
          <Button
            color="error" variant="contained"
            disabled={cancelReason.trim().length < 3 || cancelMutation.isPending}
            onClick={() => cancelTarget && cancelMutation.mutate({ id: cancelTarget.id, reason: cancelReason.trim() })}
          >
            Cancelar pedido
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
