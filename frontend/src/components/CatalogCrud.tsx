import { zodResolver } from '@hookform/resolvers/zod';
import DeleteIcon from '@mui/icons-material/Delete';
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
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiErrorMessage } from '@/api/client';
import type { createCrudApi } from '@/api/crud';
import type { CatalogItem } from '@/api/types';
import ConfirmDialog from '@/components/ConfirmDialog';
import PageHeader from '@/components/PageHeader';
import SearchBar from '@/components/SearchBar';
import { useAuth } from '@/auth/AuthContext';

const schema = z.object({
  code: z.string().min(1, 'Obrigatório').max(30),
  name: z.string().min(1, 'Obrigatório').max(120),
  description: z.string().max(500).optional().or(z.literal('')),
  status: z.enum(['ativo', 'inativo']),
});
type FormData = z.infer<typeof schema>;

interface CatalogCrudProps {
  title: string;
  subtitle?: string;
  api: ReturnType<typeof createCrudApi<CatalogItem>>;
  queryKey: string;
  permission: string;
}

export default function CatalogCrud({ title, subtitle, api, queryKey, permission }: CatalogCrudProps) {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<CatalogItem | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [toDelete, setToDelete] = useState<CatalogItem | null>(null);

  const canEdit = hasPermission(`${permission}:update`) || hasPermission(`${permission}:create`);
  const canDelete = hasPermission(`${permission}:delete`);

  const { data, isFetching } = useQuery({
    queryKey: [queryKey, page, pageSize, search],
    queryFn: () => api.list({ page: page + 1, size: pageSize, q: search }),
  });

  const { register, handleSubmit, reset, setValue, watch, formState: { errors, isSubmitting } } =
    useForm<FormData>({
      resolver: zodResolver(schema),
      defaultValues: { code: '', name: '', description: '', status: 'ativo' },
    });

  const openCreate = () => {
    setEditing(null);
    reset({ code: '', name: '', description: '', status: 'ativo' });
    setDialogOpen(true);
  };

  const openEdit = (item: CatalogItem) => {
    setEditing(item);
    reset({
      code: item.code,
      name: item.name,
      description: item.description ?? '',
      status: item.status,
    });
    setDialogOpen(true);
  };

  const saveMutation = useMutation({
    mutationFn: (values: FormData) =>
      editing ? api.update(editing.id, values) : api.create(values),
    onSuccess: () => {
      enqueueSnackbar(editing ? 'Registro atualizado' : 'Registro criado', { variant: 'success' });
      qc.invalidateQueries({ queryKey: [queryKey] });
      setDialogOpen(false);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.remove(id),
    onSuccess: () => {
      enqueueSnackbar('Registro excluído', { variant: 'success' });
      qc.invalidateQueries({ queryKey: [queryKey] });
      setToDelete(null);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<CatalogItem>[] = [
    { field: 'code', headerName: 'Código', width: 130 },
    { field: 'name', headerName: 'Nome', flex: 1, minWidth: 180 },
    { field: 'description', headerName: 'Descrição', flex: 1, minWidth: 180 },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
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
          {canEdit && (
            <IconButton size="small" onClick={() => openEdit(p.row)}>
              <EditIcon fontSize="small" />
            </IconButton>
          )}
          {canDelete && (
            <IconButton size="small" color="error" onClick={() => setToDelete(p.row)}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          )}
        </>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title={title}
        subtitle={subtitle}
        actionLabel={canEdit ? 'Novo' : undefined}
        onAction={canEdit ? openCreate : undefined}
      />

      <SearchBar
        placeholder="Buscar por código ou nome..."
        onSearch={(v) => {
          setPage(0);
          setSearch(v);
        }}
      />

      <Box sx={{ height: 560, mt: 2 }}>
        <DataGrid
          rows={data?.items ?? []}
          columns={columns}
          loading={isFetching}
          rowCount={data?.total ?? 0}
          paginationMode="server"
          paginationModel={{ page, pageSize }}
          onPaginationModelChange={(m) => {
            setPage(m.page);
            setPageSize(m.pageSize);
          }}
          pageSizeOptions={[10, 20, 50]}
          disableColumnMenu
          disableRowSelectionOnClick
          sx={{ bgcolor: 'background.paper' }}
        />
      </Box>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit((v) => saveMutation.mutate(v))}>
          <DialogTitle>{editing ? 'Editar' : 'Novo'} registro</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="Código"
                {...register('code')}
                error={!!errors.code}
                helperText={errors.code?.message}
              />
              <TextField
                label="Nome"
                {...register('name')}
                error={!!errors.name}
                helperText={errors.name?.message}
              />
              <TextField label="Descrição" multiline rows={2} {...register('description')} />
              <TextField
                select
                label="Status"
                value={watch('status')}
                onChange={(e) => setValue('status', e.target.value as 'ativo' | 'inativo')}
              >
                <MenuItem value="ativo">Ativo</MenuItem>
                <MenuItem value="inativo">Inativo</MenuItem>
              </TextField>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
            <Button type="submit" variant="contained" disabled={isSubmitting || saveMutation.isPending}>
              Salvar
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      <ConfirmDialog
        open={!!toDelete}
        title="Excluir registro"
        message={`Deseja realmente excluir "${toDelete?.name}"?`}
        confirmLabel="Excluir"
        loading={deleteMutation.isPending}
        onClose={() => setToDelete(null)}
        onConfirm={() => toDelete && deleteMutation.mutate(toDelete.id)}
      />
    </Box>
  );
}
