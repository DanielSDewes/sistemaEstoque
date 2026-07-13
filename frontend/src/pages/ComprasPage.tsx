import CancelIcon from '@mui/icons-material/Cancel';
import MoveToInboxIcon from '@mui/icons-material/MoveToInbox';
import SendIcon from '@mui/icons-material/Send';
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
import { useEffect, useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import { purchaseOrdersApi, type ReceiveItemPayload } from '@/api/endpoints';
import type { PurchaseOrder, PurchaseOrderStatus } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import ConfirmDialog from '@/components/ConfirmDialog';
import PageHeader from '@/components/PageHeader';
import SearchBar from '@/components/SearchBar';
import PurchaseFormDialog from '@/pages/compras/PurchaseFormDialog';

const money = (n: number | null | undefined) =>
  n == null ? '—' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

type ChipColor = 'default' | 'info' | 'warning' | 'success' | 'error';

const STATUS_LABEL: Record<PurchaseOrderStatus, { label: string; color: ChipColor }> = {
  rascunho: { label: 'Rascunho', color: 'default' },
  emitido: { label: 'Emitido', color: 'info' },
  parcial: { label: 'Parcial', color: 'warning' },
  recebido: { label: 'Recebido', color: 'success' },
  cancelado: { label: 'Cancelado', color: 'error' },
};

function DetailDialog({ po, onClose }: { po: PurchaseOrder | null; onClose: () => void }) {
  if (!po) return null;
  return (
    <Dialog open={!!po} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Compra {po.number}
        <Chip size="small" sx={{ ml: 1 }} color={STATUS_LABEL[po.status].color} label={STATUS_LABEL[po.status].label} />
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Fornecedor: {po.supplier_name} · {new Date(po.order_date).toLocaleDateString('pt-BR')}
          {po.expected_date && ` · previsão ${new Date(po.expected_date).toLocaleDateString('pt-BR')}`}
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Produto</TableCell>
              <TableCell align="right">Qtd</TableCell>
              <TableCell align="right">Recebido</TableCell>
              <TableCell align="right">Custo unit.</TableCell>
              <TableCell align="right">Subtotal</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {po.items.map((it) => (
              <TableRow key={it.id}>
                <TableCell>{it.product_name}</TableCell>
                <TableCell align="right">{it.quantity}</TableCell>
                <TableCell align="right">{it.received_quantity}</TableCell>
                <TableCell align="right">{money(it.unit_cost)}</TableCell>
                <TableCell align="right">{money(it.line_total)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <Box sx={{ mt: 2, ml: 'auto', maxWidth: 320 }}>
          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">Total dos itens</Typography>
            <Typography variant="body2">{money(po.total_amount)}</Typography>
          </Stack>
          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">Custo extra</Typography>
            <Typography variant="body2">{money(po.extra_cost)}</Typography>
          </Stack>
          <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.5 }}>
            <Typography variant="subtitle1" fontWeight={700}>Total</Typography>
            <Typography variant="subtitle1" fontWeight={700}>{money(po.total_amount + po.extra_cost)}</Typography>
          </Stack>
        </Box>
        {po.notes && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>Obs.: {po.notes}</Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Fechar</Button>
      </DialogActions>
    </Dialog>
  );
}

function ReceiveDialog({
  po,
  onClose,
  onConfirm,
  loading,
}: {
  po: PurchaseOrder | null;
  onClose: () => void;
  onConfirm: (items: ReceiveItemPayload[]) => void;
  loading: boolean;
}) {
  const [qty, setQty] = useState<Record<number, string>>({});

  useEffect(() => {
    if (po) {
      // Default each row to its full pending quantity.
      const initial: Record<number, string> = {};
      po.items.forEach((it) => {
        initial[it.id] = String(it.pending_quantity);
      });
      setQty(initial);
    }
  }, [po]);

  if (!po) return null;

  const items: ReceiveItemPayload[] = po.items
    .map((it) => ({ item_id: it.id, quantity: Number(qty[it.id]) || 0 }))
    .filter((r) => r.quantity > 0);

  const overReceiving = po.items.some(
    (it) => (Number(qty[it.id]) || 0) > it.pending_quantity,
  );

  return (
    <Dialog open={!!po} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Receber compra {po.number}</DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Informe as quantidades recebidas. Cada recebimento gera entradas em estoque
          e atualiza o custo médio.
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Produto</TableCell>
              <TableCell align="right">Pendente</TableCell>
              <TableCell align="right" width={130}>Receber</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {po.items.map((it) => (
              <TableRow key={it.id}>
                <TableCell>{it.product_name}</TableCell>
                <TableCell align="right">{it.pending_quantity}</TableCell>
                <TableCell align="right">
                  <TextField
                    size="small" type="number" value={qty[it.id] ?? ''}
                    onChange={(e) => setQty((prev) => ({ ...prev, [it.id]: e.target.value }))}
                    inputProps={{ min: 0, max: it.pending_quantity, step: 'any' }}
                    error={(Number(qty[it.id]) || 0) > it.pending_quantity}
                    disabled={it.pending_quantity <= 0}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Voltar</Button>
        <Button
          variant="contained"
          disabled={items.length === 0 || overReceiving || loading}
          onClick={() => onConfirm(items)}
        >
          Confirmar recebimento
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default function ComprasPage() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<PurchaseOrderStatus | ''>('');
  const [formOpen, setFormOpen] = useState(false);
  const [detail, setDetail] = useState<PurchaseOrder | null>(null);
  const [placeTarget, setPlaceTarget] = useState<PurchaseOrder | null>(null);
  const [receiveTarget, setReceiveTarget] = useState<PurchaseOrder | null>(null);
  const [cancelTarget, setCancelTarget] = useState<PurchaseOrder | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const canCreate = hasPermission('purchase:create');
  const canPlace = hasPermission('purchase:place');
  const canReceive = hasPermission('purchase:receive');
  const canCancel = hasPermission('purchase:cancel');

  const { data, isFetching } = useQuery({
    queryKey: ['purchase-orders', page, pageSize, search, status],
    queryFn: () =>
      purchaseOrdersApi.list({
        page: page + 1,
        size: pageSize,
        q: search,
        status: status || undefined,
      }),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['purchase-orders'] });
  const onError = (e: unknown) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' });

  const placeMutation = useMutation({
    mutationFn: (id: number) => purchaseOrdersApi.place(id),
    onSuccess: () => {
      enqueueSnackbar('Pedido de compra emitido', { variant: 'success' });
      invalidate();
      setPlaceTarget(null);
    },
    onError,
  });

  const receiveMutation = useMutation({
    mutationFn: ({ id, items }: { id: number; items: ReceiveItemPayload[] }) =>
      purchaseOrdersApi.receive(id, items),
    onSuccess: (po) => {
      enqueueSnackbar(
        po.status === 'recebido' ? 'Recebimento concluído, estoque atualizado' : 'Recebimento parcial registrado',
        { variant: 'success' },
      );
      invalidate();
      setReceiveTarget(null);
    },
    onError,
  });

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => purchaseOrdersApi.cancel(id, reason),
    onSuccess: () => {
      enqueueSnackbar('Pedido de compra cancelado', { variant: 'success' });
      invalidate();
      setCancelTarget(null);
      setCancelReason('');
    },
    onError,
  });

  const columns: GridColDef<PurchaseOrder>[] = [
    { field: 'number', headerName: 'Compra', width: 130 },
    { field: 'supplier_name', headerName: 'Fornecedor', flex: 1, minWidth: 180 },
    {
      field: 'order_date',
      headerName: 'Data',
      width: 120,
      valueGetter: (v) => new Date(v as string).toLocaleDateString('pt-BR'),
    },
    { field: 'items', headerName: 'Itens', width: 80, valueGetter: (_v, row) => row.items.length },
    {
      field: 'status',
      headerName: 'Status',
      width: 130,
      renderCell: (p) => (
        <Chip size="small" color={STATUS_LABEL[p.value as PurchaseOrderStatus].color} label={STATUS_LABEL[p.value as PurchaseOrderStatus].label} />
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
      width: 170,
      sortable: false,
      renderCell: (p) => (
        <>
          <IconButton size="small" onClick={() => setDetail(p.row)} title="Detalhes">
            <VisibilityIcon fontSize="small" />
          </IconButton>
          {canPlace && p.row.status === 'rascunho' && (
            <IconButton size="small" color="info" onClick={() => setPlaceTarget(p.row)} title="Emitir">
              <SendIcon fontSize="small" />
            </IconButton>
          )}
          {canReceive && (p.row.status === 'emitido' || p.row.status === 'parcial') && (
            <IconButton size="small" color="success" onClick={() => setReceiveTarget(p.row)} title="Receber">
              <MoveToInboxIcon fontSize="small" />
            </IconButton>
          )}
          {canCancel && (p.row.status === 'rascunho' || p.row.status === 'emitido') && (
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
        title="Pedidos de Compra"
        subtitle="Compras a fornecedores; o recebimento gera entrada em estoque"
        actionLabel={canCreate ? 'Nova compra' : undefined}
        onAction={canCreate ? () => setFormOpen(true) : undefined}
      />
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <SearchBar placeholder="Buscar por número ou fornecedor..." onSearch={(v) => { setPage(0); setSearch(v); }} />
        <TextField
          select size="small" label="Status" value={status}
          onChange={(e) => { setPage(0); setStatus(e.target.value as PurchaseOrderStatus | ''); }}
          sx={{ minWidth: 180, bgcolor: 'background.paper' }}
        >
          <MenuItem value="">Todos</MenuItem>
          <MenuItem value="rascunho">Rascunho</MenuItem>
          <MenuItem value="emitido">Emitido</MenuItem>
          <MenuItem value="parcial">Parcial</MenuItem>
          <MenuItem value="recebido">Recebido</MenuItem>
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

      <PurchaseFormDialog open={formOpen} onClose={() => setFormOpen(false)} />
      <DetailDialog po={detail} onClose={() => setDetail(null)} />
      <ReceiveDialog
        po={receiveTarget}
        loading={receiveMutation.isPending}
        onClose={() => setReceiveTarget(null)}
        onConfirm={(items) => receiveTarget && receiveMutation.mutate({ id: receiveTarget.id, items })}
      />

      <ConfirmDialog
        open={!!placeTarget}
        title="Emitir pedido de compra"
        message={`Emitir a compra ${placeTarget?.number}? Ela ficará disponível para recebimento.`}
        confirmLabel="Emitir"
        loading={placeMutation.isPending}
        onClose={() => setPlaceTarget(null)}
        onConfirm={() => placeTarget && placeMutation.mutate(placeTarget.id)}
      />

      <Dialog open={!!cancelTarget} onClose={() => setCancelTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Cancelar compra {cancelTarget?.number}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Somente pedidos sem recebimento podem ser cancelados.
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
            Cancelar compra
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
