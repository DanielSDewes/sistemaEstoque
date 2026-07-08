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
import { customersApi, ordersApi, productsApi } from '@/api/endpoints';

interface Props {
  open: boolean;
  onClose: () => void;
}

interface ItemRow {
  product_id: number | '';
  quantity: string;
  unit_price: string;
}

const money = (n: number) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const EMPTY_ROW: ItemRow = { product_id: '', quantity: '1', unit_price: '' };

export default function OrderFormDialog({ open, onClose }: Props) {
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [customerId, setCustomerId] = useState<number | ''>('');
  const [notes, setNotes] = useState('');
  const [extraCost, setExtraCost] = useState('');
  const [rows, setRows] = useState<ItemRow[]>([{ ...EMPTY_ROW }]);

  const { data: customers } = useQuery({
    queryKey: ['customers', 'all'],
    queryFn: () => customersApi.list({ size: 200 }),
    enabled: open,
  });
  const { data: products } = useQuery({
    queryKey: ['products', 'all'],
    queryFn: () => productsApi.list({ size: 200 }),
    enabled: open,
  });

  useEffect(() => {
    if (open) {
      setCustomerId('');
      setNotes('');
      setExtraCost('');
      setRows([{ ...EMPTY_ROW }]);
    }
  }, [open]);

  const findProduct = (id: number | '') => products?.items.find((p) => p.id === id);

  const updateRow = (i: number, field: keyof ItemRow, value: string) =>
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));

  // Selecting a product defaults the unit price to its registered sale price.
  const selectProduct = (i: number, value: string) => {
    const p = products?.items.find((x) => x.id === Number(value));
    setRows((prev) =>
      prev.map((r, idx) =>
        idx === i
          ? {
              ...r,
              product_id: value === '' ? '' : Number(value),
              unit_price: p ? String(p.sale_price) : r.unit_price,
            }
          : r,
      ),
    );
  };

  const lineTotal = (r: ItemRow) => (Number(r.quantity) || 0) * (Number(r.unit_price) || 0);
  const total = rows.reduce((sum, r) => sum + lineTotal(r), 0);
  const estimatedCost = rows.reduce((sum, r) => {
    const p = findProduct(r.product_id);
    return sum + (Number(r.quantity) || 0) * (p ? p.average_cost : 0);
  }, 0);
  const extra = Number(extraCost) || 0;
  const estimatedProfit = total - estimatedCost - extra;

  const create = useMutation({
    mutationFn: () =>
      ordersApi.create({
        customer_id: Number(customerId),
        notes: notes.trim() || null,
        extra_cost: extra,
        items: rows
          .filter((r) => r.product_id !== '' && Number(r.quantity) > 0)
          .map((r) => ({
            product_id: Number(r.product_id),
            quantity: Number(r.quantity),
            unit_price: Number(r.unit_price) || 0,
          })),
      }),
    onSuccess: () => {
      enqueueSnackbar('Pedido criado (rascunho)', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['orders'] });
      onClose();
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const validItems = rows.filter((r) => r.product_id !== '' && Number(r.quantity) > 0);
  const canSave = customerId !== '' && validItems.length > 0;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Novo pedido</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField
            select label="Cliente" value={customerId}
            onChange={(e) => setCustomerId(Number(e.target.value))}
          >
            {customers?.items.map((c) => (
              <MenuItem key={c.id} value={c.id}>{c.name} — {c.phone}</MenuItem>
            ))}
          </TextField>

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ minWidth: 220 }}>Produto</TableCell>
                <TableCell width={110}>Qtd</TableCell>
                <TableCell width={140}>Preço unit.</TableCell>
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
                      size="small" type="number" value={r.unit_price}
                      onChange={(e) => updateRow(i, 'unit_price', e.target.value)}
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
            <Stack direction="row" justifyContent="space-between"><Typography variant="body2" color="text.secondary">Receita</Typography><Typography variant="body2">{money(total)}</Typography></Stack>
            <Stack direction="row" justifyContent="space-between"><Typography variant="body2" color="text.secondary">Custo estimado (produtos)</Typography><Typography variant="body2">{money(estimatedCost)}</Typography></Stack>
            <Stack direction="row" justifyContent="space-between"><Typography variant="body2" color="text.secondary">Custo extra</Typography><Typography variant="body2">{money(extra)}</Typography></Stack>
            <Stack direction="row" justifyContent="space-between" sx={{ mt: 0.5 }}>
              <Typography variant="subtitle1" fontWeight={700}>Lucro estimado</Typography>
              <Typography variant="subtitle1" fontWeight={700} color={estimatedProfit >= 0 ? 'success.main' : 'error.main'}>
                {money(estimatedProfit)}
              </Typography>
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
