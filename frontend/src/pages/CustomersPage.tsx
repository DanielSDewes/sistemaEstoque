import { zodResolver } from '@hookform/resolvers/zod';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  IconButton,
  Radio,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiErrorMessage } from '@/api/client';
import { customersApi } from '@/api/endpoints';
import type { Customer } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import PageHeader from '@/components/PageHeader';
import SearchBar from '@/components/SearchBar';
import CustomerDetailDialog from '@/pages/customers/CustomerDetailDialog';

const schema = z.object({
  name: z.string().min(2, 'Obrigatório').max(200),
  phone: z.string().min(8, 'Telefone obrigatório').max(30),
  document: z.string().max(20).optional().or(z.literal('')),
  email: z.string().email('E-mail inválido').optional().or(z.literal('')),
  notes: z.string().max(1000).optional().or(z.literal('')),
});
type FormData = z.infer<typeof schema>;

const EMPTY: FormData = { name: '', phone: '', document: '', email: '', notes: '' };

interface AddressForm {
  label: string;
  street: string;
  number: string;
  complement: string;
  district: string;
  city: string;
  state: string;
  zip_code: string;
  is_primary: boolean;
}

const EMPTY_ADDRESS: AddressForm = {
  label: '', street: '', number: '', complement: '', district: '', city: '', state: '', zip_code: '',
  is_primary: false,
};

const orNull = (v: string) => (v.trim() ? v.trim() : null);

const isAddressFilled = (a: AddressForm) =>
  [a.label, a.street, a.number, a.complement, a.district, a.city, a.state, a.zip_code].some(
    (v) => v.trim() !== '',
  );

export default function CustomersPage() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [addresses, setAddresses] = useState<AddressForm[]>([]);
  const [detail, setDetail] = useState<Customer | null>(null);

  const canCreate = hasPermission('customer:create');
  const canEdit = hasPermission('customer:update');

  const { data, isFetching } = useQuery({
    queryKey: ['customers', page, pageSize, search],
    queryFn: () => customersApi.list({ page: page + 1, size: pageSize, q: search }),
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  });

  useEffect(() => {
    reset(
      editing
        ? {
            name: editing.name,
            phone: editing.phone,
            document: editing.document ?? '',
            email: editing.email ?? '',
            notes: editing.notes ?? '',
          }
        : EMPTY,
    );
    setAddresses(
      editing
        ? editing.addresses.map((a) => ({
            label: a.label ?? '',
            street: a.street ?? '',
            number: a.number ?? '',
            complement: a.complement ?? '',
            district: a.district ?? '',
            city: a.city ?? '',
            state: a.state ?? '',
            zip_code: a.zip_code ?? '',
            is_primary: a.is_primary,
          }))
        : [],
    );
  }, [editing, reset]);

  const addAddress = () =>
    setAddresses((prev) => [...prev, { ...EMPTY_ADDRESS, is_primary: prev.length === 0 }]);

  const updateAddress = (index: number, field: keyof AddressForm, value: string) =>
    setAddresses((prev) => prev.map((a, i) => (i === index ? { ...a, [field]: value } : a)));

  const setPrimary = (index: number) =>
    setAddresses((prev) => prev.map((a, i) => ({ ...a, is_primary: i === index })));

  const removeAddress = (index: number) =>
    setAddresses((prev) => {
      const next = prev.filter((_, i) => i !== index);
      if (next.length && !next.some((a) => a.is_primary)) next[0].is_primary = true;
      return next;
    });

  const mutation = useMutation({
    mutationFn: (values: FormData) => {
      const filled = addresses.filter(isAddressFilled);
      if (filled.length && !filled.some((a) => a.is_primary)) filled[0].is_primary = true;
      const payload = {
        name: values.name,
        phone: values.phone,
        document: orNull(values.document ?? ''),
        email: orNull(values.email ?? ''),
        notes: orNull(values.notes ?? ''),
        addresses: filled.map((a) => ({
          label: orNull(a.label),
          street: orNull(a.street),
          number: orNull(a.number),
          complement: orNull(a.complement),
          district: orNull(a.district),
          city: orNull(a.city),
          state: orNull(a.state),
          zip_code: orNull(a.zip_code),
          is_primary: a.is_primary,
        })),
      };
      return editing ? customersApi.update(editing.id, payload) : customersApi.create(payload);
    },
    onSuccess: () => {
      enqueueSnackbar('Cliente salvo', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['customers'] });
      setOpen(false);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<Customer>[] = [
    { field: 'name', headerName: 'Nome', flex: 1, minWidth: 180 },
    { field: 'phone', headerName: 'Telefone', width: 150 },
    { field: 'document', headerName: 'Documento', width: 150 },
    { field: 'email', headerName: 'E-mail', flex: 1, minWidth: 160 },
    {
      field: 'status',
      headerName: 'Status',
      width: 110,
      renderCell: (p) => (
        <Chip
          size="small"
          label={p.value === 'ativo' ? 'Ativo' : 'Inativo'}
          color={p.value === 'ativo' ? 'success' : 'default'}
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 110,
      sortable: false,
      renderCell: (p) => (
        <>
          <IconButton size="small" onClick={() => setDetail(p.row)} title="Detalhes / histórico">
            <VisibilityIcon fontSize="small" />
          </IconButton>
          {canEdit && (
            <IconButton size="small" onClick={() => { setEditing(p.row); setOpen(true); }} title="Editar">
              <EditIcon fontSize="small" />
            </IconButton>
          )}
        </>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Clientes"
        subtitle="Cadastro de clientes, endereços e histórico de vendas"
        actionLabel={canCreate ? 'Novo cliente' : undefined}
        onAction={canCreate ? () => { setEditing(null); setOpen(true); } : undefined}
      />
      <SearchBar placeholder="Buscar por nome, telefone ou documento..." onSearch={(v) => { setPage(0); setSearch(v); }} />
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

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="md" fullWidth>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))}>
          <DialogTitle>{editing ? 'Editar' : 'Novo'} cliente</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <TextField label="Nome *" fullWidth {...register('name')} error={!!errors.name} helperText={errors.name?.message} />
                <TextField label="Telefone *" fullWidth {...register('phone')} error={!!errors.phone} helperText={errors.phone?.message} />
              </Stack>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <TextField label="Documento (CPF/CNPJ)" fullWidth {...register('document')} />
                <TextField label="E-mail" fullWidth {...register('email')} error={!!errors.email} helperText={errors.email?.message} />
              </Stack>
              <TextField label="Observações" fullWidth multiline minRows={2} {...register('notes')} />

              <Divider textAlign="left">
                <Typography variant="subtitle2" color="text.secondary">Endereços</Typography>
              </Divider>

              {addresses.map((a, i) => (
                <Box key={i} sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 2 }}>
                  <Stack spacing={1.5}>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems="center">
                      <TextField size="small" label="Rótulo" value={a.label} onChange={(e) => updateAddress(i, 'label', e.target.value)} sx={{ minWidth: 140 }} />
                      <TextField size="small" label="Logradouro" fullWidth value={a.street} onChange={(e) => updateAddress(i, 'street', e.target.value)} />
                      <TextField size="small" label="Nº" value={a.number} onChange={(e) => updateAddress(i, 'number', e.target.value)} sx={{ width: 100 }} />
                    </Stack>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                      <TextField size="small" label="Complemento" fullWidth value={a.complement} onChange={(e) => updateAddress(i, 'complement', e.target.value)} />
                      <TextField size="small" label="Bairro" fullWidth value={a.district} onChange={(e) => updateAddress(i, 'district', e.target.value)} />
                    </Stack>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems="center">
                      <TextField size="small" label="Cidade" fullWidth value={a.city} onChange={(e) => updateAddress(i, 'city', e.target.value)} />
                      <TextField size="small" label="UF" value={a.state} onChange={(e) => updateAddress(i, 'state', e.target.value)} sx={{ width: 90 }} />
                      <TextField size="small" label="CEP" value={a.zip_code} onChange={(e) => updateAddress(i, 'zip_code', e.target.value)} sx={{ width: 130 }} />
                      <FormControlLabel
                        control={<Radio checked={a.is_primary} onChange={() => setPrimary(i)} />}
                        label="Principal"
                      />
                      <IconButton size="small" color="error" onClick={() => removeAddress(i)} title="Remover endereço">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </Stack>
                </Box>
              ))}
              <Box>
                <Button startIcon={<AddIcon />} onClick={addAddress}>Adicionar endereço</Button>
              </Box>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancelar</Button>
            <Button type="submit" variant="contained" disabled={mutation.isPending}>Salvar</Button>
          </DialogActions>
        </form>
      </Dialog>

      <CustomerDetailDialog open={!!detail} customer={detail} onClose={() => setDetail(null)} />
    </Box>
  );
}
