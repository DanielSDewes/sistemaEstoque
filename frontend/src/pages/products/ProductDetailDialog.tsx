import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import {
  Avatar,
  Box,
  Button,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  MenuItem,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useState } from 'react';

import { apiErrorMessage, assetUrl } from '@/api/client';
import {
  corridorsApi,
  productExtrasApi,
  productHistory,
  shelvesApi,
  suppliersApi,
} from '@/api/endpoints';
import type { Product } from '@/api/types';

interface Props {
  open: boolean;
  product: Product | null;
  onClose: () => void;
}

const money = (n: number | null | undefined) =>
  n == null ? '—' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

function SuppliersTab({ productId }: { productId: number }) {
  const qc = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const { data: links } = useQuery({
    queryKey: ['product-suppliers', productId],
    queryFn: () => productExtrasApi.suppliers(productId),
  });
  const { data: suppliers } = useQuery({
    queryKey: ['suppliers', 'all'],
    queryFn: () => suppliersApi.list({ size: 200 }),
  });
  const [supplierId, setSupplierId] = useState<number | ''>('');
  const [price, setPrice] = useState('');

  const invalidate = () => qc.invalidateQueries({ queryKey: ['product-suppliers', productId] });
  const onError = (e: unknown) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' });

  const link = useMutation({
    mutationFn: () =>
      productExtrasApi.linkSupplier({
        product_id: productId,
        supplier_id: Number(supplierId),
        current_price: price ? Number(price) : null,
      }),
    onSuccess: () => { invalidate(); setSupplierId(''); setPrice(''); },
    onError,
  });
  const setPrimary = useMutation({
    mutationFn: (id: number) => productExtrasApi.updateSupplier(id, { is_primary: true }),
    onSuccess: invalidate,
    onError,
  });
  const unlink = useMutation({
    mutationFn: (id: number) => productExtrasApi.unlinkSupplier(id),
    onSuccess: invalidate,
    onError,
  });

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <TextField
          select size="small" label="Fornecedor" value={supplierId}
          onChange={(e) => setSupplierId(Number(e.target.value))} sx={{ minWidth: 220 }}
        >
          {suppliers?.items.map((s) => (
            <MenuItem key={s.id} value={s.id}>{s.trade_name || s.legal_name}</MenuItem>
          ))}
        </TextField>
        <TextField size="small" label="Preço atual" type="number" value={price}
          onChange={(e) => setPrice(e.target.value)} sx={{ width: 140 }} />
        <Button variant="contained" startIcon={<AddIcon />} disabled={!supplierId || link.isPending}
          onClick={() => link.mutate()}>Vincular</Button>
      </Stack>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Fornecedor</TableCell><TableCell>Preço atual</TableCell>
            <TableCell>Preço médio</TableCell><TableCell>Principal</TableCell><TableCell /></TableRow>
        </TableHead>
        <TableBody>
          {links?.map((l) => (
            <TableRow key={l.id}>
              <TableCell>{l.supplier.trade_name || l.supplier.legal_name}</TableCell>
              <TableCell>{money(l.current_price)}</TableCell>
              <TableCell>{money(l.average_price)}</TableCell>
              <TableCell>
                <IconButton size="small" color="warning" onClick={() => setPrimary.mutate(l.id)}>
                  {l.is_primary ? <StarIcon fontSize="small" /> : <StarBorderIcon fontSize="small" />}
                </IconButton>
              </TableCell>
              <TableCell align="right">
                <IconButton size="small" color="error" onClick={() => unlink.mutate(l.id)}>
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
          {!links?.length && (
            <TableRow><TableCell colSpan={5}><Typography variant="body2" color="text.secondary">Nenhum fornecedor vinculado.</Typography></TableCell></TableRow>
          )}
        </TableBody>
      </Table>
    </Box>
  );
}

function BatchesTab({ productId }: { productId: number }) {
  const qc = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const { data: batches } = useQuery({
    queryKey: ['batches', productId],
    queryFn: () => productExtrasApi.batches(productId),
  });
  const [lot, setLot] = useState('');
  const [expiry, setExpiry] = useState('');
  const invalidate = () => qc.invalidateQueries({ queryKey: ['batches', productId] });
  const onError = (e: unknown) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' });

  const create = useMutation({
    mutationFn: () => productExtrasApi.createBatch({
      product_id: productId, lot_number: lot, expiry_date: expiry || null,
    }),
    onSuccess: () => { invalidate(); setLot(''); setExpiry(''); },
    onError,
  });
  const remove = useMutation({
    mutationFn: (id: number) => productExtrasApi.deleteBatch(id), onSuccess: invalidate, onError,
  });

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <TextField size="small" label="Lote" value={lot} onChange={(e) => setLot(e.target.value)} />
        <TextField size="small" label="Validade" type="date" InputLabelProps={{ shrink: true }}
          value={expiry} onChange={(e) => setExpiry(e.target.value)} />
        <Button variant="contained" startIcon={<AddIcon />} disabled={!lot || create.isPending}
          onClick={() => create.mutate()}>Adicionar</Button>
      </Stack>
      <Table size="small">
        <TableHead><TableRow><TableCell>Lote</TableCell><TableCell>Validade</TableCell><TableCell /></TableRow></TableHead>
        <TableBody>
          {batches?.map((b) => (
            <TableRow key={b.id}>
              <TableCell>{b.lot_number}</TableCell>
              <TableCell>{b.expiry_date ?? '—'}</TableCell>
              <TableCell align="right">
                <IconButton size="small" color="error" onClick={() => remove.mutate(b.id)}>
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
          {!batches?.length && (
            <TableRow><TableCell colSpan={3}><Typography variant="body2" color="text.secondary">Nenhum lote cadastrado.</Typography></TableCell></TableRow>
          )}
        </TableBody>
      </Table>
    </Box>
  );
}

function LocationsTab({ productId }: { productId: number }) {
  const qc = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const { data: locations } = useQuery({
    queryKey: ['product-locations', productId],
    queryFn: () => productExtrasApi.locations(productId),
  });
  const { data: corridors } = useQuery({ queryKey: ['corridors', 'all'], queryFn: () => corridorsApi.list({ size: 200 }) });
  const { data: shelves } = useQuery({ queryKey: ['shelves', 'all'], queryFn: () => shelvesApi.list({ size: 500 }) });
  const [corridorId, setCorridorId] = useState<number | ''>('');
  const [shelfId, setShelfId] = useState<number | ''>('');
  const invalidate = () => qc.invalidateQueries({ queryKey: ['product-locations', productId] });
  const onError = (e: unknown) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' });

  const assign = useMutation({
    mutationFn: () => productExtrasApi.assignLocation({
      product_id: productId, corridor_id: Number(corridorId), shelf_id: Number(shelfId),
    }),
    onSuccess: () => { invalidate(); setShelfId(''); },
    onError,
  });
  const remove = useMutation({
    mutationFn: (id: number) => productExtrasApi.removeLocation(id), onSuccess: invalidate, onError,
  });

  const shelvesForCorridor = shelves?.items.filter((s) => s.corridor_id === corridorId) ?? [];

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <TextField select size="small" label="Corredor" value={corridorId} sx={{ minWidth: 160 }}
          onChange={(e) => { setCorridorId(Number(e.target.value)); setShelfId(''); }}>
          {corridors?.items.map((c) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Prateleira" value={shelfId} sx={{ minWidth: 160 }}
          disabled={!corridorId} onChange={(e) => setShelfId(Number(e.target.value))}>
          {shelvesForCorridor.map((s) => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
        </TextField>
        <Button variant="contained" startIcon={<AddIcon />} disabled={!shelfId || assign.isPending}
          onClick={() => assign.mutate()}>Alocar</Button>
      </Stack>
      <Table size="small">
        <TableHead><TableRow><TableCell>Corredor</TableCell><TableCell>Prateleira</TableCell><TableCell>Saldo no local</TableCell><TableCell /></TableRow></TableHead>
        <TableBody>
          {locations?.map((l) => (
            <TableRow key={l.id}>
              <TableCell>{l.corridor.name}</TableCell>
              <TableCell>{l.shelf.name}</TableCell>
              <TableCell><Chip size="small" label={l.stock_balance} /></TableCell>
              <TableCell align="right">
                <IconButton size="small" color="error" onClick={() => remove.mutate(l.id)}>
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
          {!locations?.length && (
            <TableRow><TableCell colSpan={4}><Typography variant="body2" color="text.secondary">Nenhuma localização.</Typography></TableCell></TableRow>
          )}
        </TableBody>
      </Table>
    </Box>
  );
}

function HistoryTab({ productId }: { productId: number }) {
  const { data } = useQuery({
    queryKey: ['product-history', productId],
    queryFn: () => productHistory(productId, { size: 50 }),
  });
  return (
    <Table size="small">
      <TableHead><TableRow><TableCell>Data</TableCell><TableCell>Tipo</TableCell><TableCell>Direção</TableCell><TableCell>Qtd</TableCell></TableRow></TableHead>
      <TableBody>
        {data?.items.map((m) => (
          <TableRow key={m.id} sx={{ opacity: m.is_cancelled ? 0.5 : 1 }}>
            <TableCell>{new Date(m.moved_at).toLocaleString('pt-BR')}</TableCell>
            <TableCell>{m.movement_type}</TableCell>
            <TableCell>
              <Chip size="small" label={m.direction} color={m.direction === 'entrada' ? 'success' : 'error'} variant="outlined" />
            </TableCell>
            <TableCell>{m.quantity}</TableCell>
          </TableRow>
        ))}
        {!data?.items.length && (
          <TableRow><TableCell colSpan={4}><Typography variant="body2" color="text.secondary">Sem movimentações.</Typography></TableCell></TableRow>
        )}
      </TableBody>
    </Table>
  );
}

export default function ProductDetailDialog({ open, product, onClose }: Props) {
  const [tab, setTab] = useState(0);
  if (!product) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" spacing={2} alignItems="center">
          <Avatar src={assetUrl(product.photo_url)} variant="rounded" sx={{ width: 48, height: 48 }}>
            {product.name[0]}
          </Avatar>
          <Box>
            <Typography variant="h6">{product.name}</Typography>
            <Typography variant="caption" color="text.secondary">
              {product.internal_code}
              {product.stock && ` · Saldo: ${product.stock.current} · Custo médio: ${money(product.average_cost)}`}
            </Typography>
          </Box>
        </Stack>
      </DialogTitle>
      <Divider />
      <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" sx={{ px: 2 }}>
        <Tab label="Fornecedores" />
        <Tab label="Lotes" />
        <Tab label="Localizações" />
        <Tab label="Histórico" />
      </Tabs>
      <DialogContent dividers>
        {tab === 0 && <SuppliersTab productId={product.id} />}
        {tab === 1 && <BatchesTab productId={product.id} />}
        {tab === 2 && <LocationsTab productId={product.id} />}
        {tab === 3 && <HistoryTab productId={product.id} />}
      </DialogContent>
    </Dialog>
  );
}
