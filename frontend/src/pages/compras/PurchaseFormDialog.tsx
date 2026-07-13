import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import {
  Box,
  Button,
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
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useEffect, useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import { productsApi, purchaseOrdersApi, suppliersApi } from '@/api/endpoints';

interface Props {
  open: boolean;
  onClose: () => void;
}

interface ItemRow {
  product_id: number | '';
  quantity: string;
  unit_cost: string;
}

const money = (n: number) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const EMPTY_ROW: ItemRow = { product_id: '', quantity: '1', unit_cost: '' };

export default function PurchaseFormDialog({ open, onClose }: Props) {
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [supplierId, setSupplierId] = useState<number | ''>('');
  const [expectedDate, setExpectedDate] = useState('');
  const [notes, setNotes] = useState('');
  const [extraCost, setExtraCost] = useState('');
  const [rows, setRows] = useState<ItemRow[]>([{ ...EMPTY_ROW }]);

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers', 'all'],
    queryFn: () => suppliersApi.list({ size: 200 }),
    enabled: open,
  });
  const { data: products } = useQuery({
    queryKey: ['products', 'all'],
    queryFn: () => productsApi.list({ size: 200 }),
    enabled: open,
  });

  useEffect(() => {
    if (open) {
      setSupplierId('');
      setExpectedDate('');
      setNotes('');
      setExtraCost('');
      setRows([{ ...EMPTY_ROW }]);
    }
  }, [open]);

  const updateRow = (i: number, field: keyof ItemRow, value: string) =>
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));

  // Selecting a product defaults the unit cost to its current average cost.
  const selectProduct = (i: number, value: string) => {
    const p = products?.items.find((x) => x.id === Number(value));
    setRows((prev) =>
      prev.map((r, idx) =>
        idx === i
          ? {
              ...r,
              product_id: value === '' ? '' : Number(value),
              unit_cost: p && p.average_cost > 0 ? String(p.average_cost) : r.unit_cost,
            }
          : r,
      ),
    );
  };

  const lineTotal = (r: ItemRow) => (Number(r.quantity) || 0) * (Number(r.unit_cost) || 0);
  const total = rows.reduce((sum, r) => sum + lineTotal(r), 0);
  const extra = Number(extraCost) || 0;

  const create = useMutation({
    mutationFn: () =>
      purchaseOrdersApi.create({
        supplier_id: Number(supplierId),
        expected_date: expectedDate || null,
        notes: notes.trim() || null,
        extra_cost: extra,
        items: rows
          .filter((r) => r.product_id !== '' && Number(r.quantity) > 0)
          .map((r) => ({
            product_id: Number(r.product_id),
            quantity: Number(r.quantity),
            unit_cost: Number(r.unit_cost) || 0,
          })),
      }),
    onSuccess: () => {
      enqueueSnackbar('Pedido de compra criado (rascunho)', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['purchase-orders'] });
      onClose();
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const validItems = rows.filter((r) => r.product_id !== '' && Number(r.quantity) > 0);
  const canSave = supplierId !== '' && validItems.length > 0;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Novo pedido de compra</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              select label="Fornecedor" value={supplierId} fullWidth
              onChange={(e) => setSupplierId(Number(e.target.value))}
            >
              {suppliers?.items.map((s) => (
                <MenuItem key={s.id} value={s.id}>{s.trade_name || s.legal_name}</MenuItem>
              ))}
            </TextField>
            <TextField
              label="Previsão de entrega" type="date" value={expectedDate}
              onChange={(e) => setExpectedDate(e.target.value)}
              InputLabelProps={{ shrink: true }} sx={{ minWidth: 200 }}
            />
          </Stack>

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ minWidth: 220 }}>Produto</TableCell>
                <TableCell width={110}>Qtd</TableCell>
                <TableCell width={140}>Custo unit.</TableCell>
                <TableCell width={130} align="right">Subtotal</TableCell>
                <TableCell width={48} />
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((r, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <TextField
                      select size="small" fullWidth value={r.product_id}
                      onChange={(e) => selectProduct(i, e.target.value)}
                    >
                      {products?.items.map((p) => (
                        <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>
                      ))}
                    </TextField>
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small" type="number" value={r.quantity}
                      onChange={(e) => updateRow(i, 'quantity', e.target.value)}
                      inputProps={{ min: 0, step: 'any' }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small" type="number" value={r.unit_cost}
                      onChange={(e) => updateRow(i, 'unit_cost', e.target.value)}
                      inputProps={{ min: 0, step: 'any' }}
                    />
                  </TableCell>
                  <TableCell align="right">{money(lineTotal(r))}</TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small" color="error" disabled={rows.length === 1}
                      onClick={() => setRows((prev) => prev.filter((_, idx) => idx !== i))}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <Box>
            <Button startIcon={<AddIcon />} onClick={() => setRows((prev) => [...prev, { ...EMPTY_ROW }])}>
              Adicionar item
            </Button>
          </Box>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="Custo extra (frete, etc.)" type="number" value={extraCost}
              onChange={(e) => setExtraCost(e.target.value)}
              inputProps={{ min: 0, step: '0.01' }} sx={{ minWidth: 200 }}
            />
            <TextField label="Observações" fullWidth multiline minRows={1} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </Stack>

          <Box sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
            <Stack direction="row" justifyContent="space-between">
              <Typography variant="body2" color="text.secondary">Total dos itens</Typography>
              <Typography variant="body2">{money(total)}</Typography>
            </Stack>
            <Stack direction="row" justifyContent="space-between">
              <Typography variant="body2" color="text.secondary">Custo extra</Typography>
              <Typography variant="body2">{money(extra)}</Typography>
            </Stack>
            <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.5 }}>
              <Typography variant="subtitle1" fontWeight={700}>Total do pedido</Typography>
              <Typography variant="subtitle1" fontWeight={700}>{money(total + extra)}</Typography>
            </Stack>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button variant="contained" disabled={!canSave || create.isPending} onClick={() => create.mutate()}>
          Salvar rascunho
        </Button>
      </DialogActions>
    </Dialog>
  );
}
