import {
  Avatar,
  Box,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { customerOrders } from '@/api/endpoints';
import type { Customer, OrderStatus } from '@/api/types';

interface Props {
  open: boolean;
  customer: Customer | null;
  onClose: () => void;
}

const money = (n: number | null | undefined) =>
  n == null ? '—' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const STATUS_LABEL: Record<OrderStatus, { label: string; color: 'default' | 'success' | 'error' }> = {
  rascunho: { label: 'Rascunho', color: 'default' },
  confirmado: { label: 'Confirmado', color: 'success' },
  cancelado: { label: 'Cancelado', color: 'error' },
};

function formatAddress(a: Customer['addresses'][number]): string {
  const parts = [
    a.street,
    a.number,
    a.complement,
    a.district,
    [a.city, a.state].filter(Boolean).join('/'),
    a.zip_code,
  ].filter(Boolean);
  return parts.join(', ') || '—';
}

function AddressesTab({ customer }: { customer: Customer }) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Rótulo</TableCell>
          <TableCell>Endereço</TableCell>
          <TableCell>Principal</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {customer.addresses.map((a) => (
          <TableRow key={a.id}>
            <TableCell>{a.label || '—'}</TableCell>
            <TableCell>{formatAddress(a)}</TableCell>
            <TableCell>
              {a.is_primary && <Chip size="small" color="primary" label="Principal" />}
            </TableCell>
          </TableRow>
        ))}
        {!customer.addresses.length && (
          <TableRow>
            <TableCell colSpan={3}>
              <Typography variant="body2" color="text.secondary">
                Nenhum endereço cadastrado.
              </Typography>
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

function HistoryTab({ customerId }: { customerId: number }) {
  const { data } = useQuery({
    queryKey: ['customer-orders', customerId],
    queryFn: () => customerOrders(customerId, { size: 50 }),
  });
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Pedido</TableCell>
          <TableCell>Data</TableCell>
          <TableCell>Itens</TableCell>
          <TableCell>Status</TableCell>
          <TableCell align="right">Total</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {data?.items.map((o) => (
          <TableRow key={o.id}>
            <TableCell>{o.number}</TableCell>
            <TableCell>{new Date(o.order_date).toLocaleDateString('pt-BR')}</TableCell>
            <TableCell>{o.items.length}</TableCell>
            <TableCell>
              <Chip size="small" color={STATUS_LABEL[o.status].color} label={STATUS_LABEL[o.status].label} />
            </TableCell>
            <TableCell align="right">{money(o.total_amount)}</TableCell>
          </TableRow>
        ))}
        {!data?.items.length && (
          <TableRow>
            <TableCell colSpan={5}>
              <Typography variant="body2" color="text.secondary">
                Nenhuma venda registrada.
              </Typography>
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

export default function CustomerDetailDialog({ open, customer, onClose }: Props) {
  const [tab, setTab] = useState(0);
  if (!customer) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" spacing={2} alignItems="center">
          <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>{customer.name[0]}</Avatar>
          <Box>
            <Typography variant="h6">{customer.name}</Typography>
            <Typography variant="caption" color="text.secondary">
              {customer.phone}
              {customer.document && ` · ${customer.document}`}
            </Typography>
          </Box>
        </Stack>
      </DialogTitle>
      <Divider />
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ px: 2 }}>
        <Tab label="Endereços" />
        <Tab label="Histórico de vendas" />
      </Tabs>
      <DialogContent dividers>
        {tab === 0 && <AddressesTab customer={customer} />}
        {tab === 1 && <HistoryTab customerId={customer.id} />}
      </DialogContent>
    </Dialog>
  );
}
