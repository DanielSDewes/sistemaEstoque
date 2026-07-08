import { zodResolver } from '@hookform/resolvers/zod';
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
  Stack,
  TextField,
} from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiErrorMessage } from '@/api/client';
import { suppliersApi } from '@/api/endpoints';
import type { Supplier } from '@/api/types';
import PageHeader from '@/components/PageHeader';
import SearchBar from '@/components/SearchBar';
import { useAuth } from '@/auth/AuthContext';

const schema = z.object({
  legal_name: z.string().min(2, 'Obrigatório').max(200),
  trade_name: z.string().max(200).optional().or(z.literal('')),
  cnpj: z.string().min(14, 'CNPJ inválido').max(18),
  city: z.string().max(120).optional().or(z.literal('')),
  state: z.string().max(2).optional().or(z.literal('')),
  email: z.string().email('E-mail inválido').optional().or(z.literal('')),
  phone: z.string().max(30).optional().or(z.literal('')),
});
type FormData = z.infer<typeof schema>;

const EMPTY: FormData = { legal_name: '', trade_name: '', cnpj: '', city: '', state: '', email: '', phone: '' };

export default function SuppliersPage() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);

  const canCreate = hasPermission('supplier:create');
  const canEdit = hasPermission('supplier:update');

  const { data, isFetching } = useQuery({
    queryKey: ['suppliers', page, pageSize, search],
    queryFn: () => suppliersApi.list({ page: page + 1, size: pageSize, q: search }),
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  });

  useEffect(() => {
    reset(
      editing
        ? {
            legal_name: editing.legal_name,
            trade_name: editing.trade_name ?? '',
            cnpj: editing.cnpj,
            city: editing.city ?? '',
            state: editing.state ?? '',
            email: editing.email ?? '',
            phone: editing.phone ?? '',
          }
        : EMPTY,
    );
  }, [editing, reset]);

  const mutation = useMutation({
    mutationFn: (values: FormData) =>
      editing ? suppliersApi.update(editing.id, values) : suppliersApi.create(values),
    onSuccess: () => {
      enqueueSnackbar('Fornecedor salvo', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['suppliers'] });
      setOpen(false);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<Supplier>[] = [
    { field: 'legal_name', headerName: 'Razão social', flex: 1, minWidth: 200 },
    { field: 'trade_name', headerName: 'Nome fantasia', width: 160 },
    { field: 'cnpj', headerName: 'CNPJ', width: 160 },
    { field: 'city', headerName: 'Cidade', width: 130 },
    { field: 'state', headerName: 'UF', width: 70 },
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
        title="Fornecedores"
        subtitle="Cadastro completo de fornecedores"
        actionLabel={canCreate ? 'Novo fornecedor' : undefined}
        onAction={canCreate ? () => { setEditing(null); setOpen(true); } : undefined}
      />
      <SearchBar placeholder="Buscar por razão social ou CNPJ..." onSearch={(v) => { setPage(0); setSearch(v); }} />
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

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))}>
          <DialogTitle>{editing ? 'Editar' : 'Novo'} fornecedor</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField label="Razão social" {...register('legal_name')} error={!!errors.legal_name} helperText={errors.legal_name?.message} />
              <TextField label="Nome fantasia" {...register('trade_name')} />
              <TextField label="CNPJ" {...register('cnpj')} error={!!errors.cnpj} helperText={errors.cnpj?.message} />
              <Stack direction="row" spacing={2}>
                <TextField label="Cidade" fullWidth {...register('city')} />
                <TextField label="UF" sx={{ width: 100 }} {...register('state')} />
              </Stack>
              <TextField label="E-mail" {...register('email')} error={!!errors.email} helperText={errors.email?.message} />
              <TextField label="Telefone" {...register('phone')} />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancelar</Button>
            <Button type="submit" variant="contained" disabled={mutation.isPending}>Salvar</Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
