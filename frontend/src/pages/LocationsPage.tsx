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
  MenuItem,
  Stack,
  Tab,
  Tabs,
  TextField,
} from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useEffect, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiErrorMessage } from '@/api/client';
import { corridorsApi, shelvesApi } from '@/api/endpoints';
import type { Shelf } from '@/api/types';
import CatalogCrud from '@/components/CatalogCrud';
import PageHeader from '@/components/PageHeader';
import { useAuth } from '@/auth/AuthContext';

const schema = z.object({
  code: z.string().min(1, 'Obrigatório').max(30),
  name: z.string().min(1, 'Obrigatório').max(120),
  corridor_id: z.coerce.number().min(1, 'Selecione um corredor'),
  capacity: z.coerce.number().min(0).optional(),
  observations: z.string().optional().or(z.literal('')),
  status: z.enum(['ativo', 'inativo']),
});
type FormData = z.infer<typeof schema>;
const EMPTY: FormData = { code: '', name: '', corridor_id: 0, capacity: 0, observations: '', status: 'ativo' };

function ShelvesTab() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Shelf | null>(null);

  const canCreate = hasPermission('shelf:create');
  const canEdit = hasPermission('shelf:update');

  const { data, isFetching } = useQuery({
    queryKey: ['shelves', page, pageSize],
    queryFn: () => shelvesApi.list({ page: page + 1, size: pageSize }),
  });
  const { data: corridors } = useQuery({ queryKey: ['corridors', 'all'], queryFn: () => corridorsApi.list({ size: 200 }) });

  const { register, handleSubmit, reset, control, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  });

  useEffect(() => {
    reset(
      editing
        ? {
            code: editing.code,
            name: editing.name,
            corridor_id: editing.corridor_id,
            capacity: editing.capacity ?? 0,
            observations: editing.observations ?? '',
            status: editing.status,
          }
        : EMPTY,
    );
  }, [editing, reset]);

  const mutation = useMutation({
    mutationFn: (values: FormData) => (editing ? shelvesApi.update(editing.id, values) : shelvesApi.create(values)),
    onSuccess: () => {
      enqueueSnackbar('Prateleira salva', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['shelves'] });
      setOpen(false);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<Shelf>[] = [
    { field: 'code', headerName: 'Código', width: 140 },
    { field: 'name', headerName: 'Nome', flex: 1, minWidth: 160 },
    { field: 'corridor', headerName: 'Corredor', width: 160, valueGetter: (_v, row) => row.corridor?.name },
    { field: 'capacity', headerName: 'Capacidade', width: 120 },
    {
      field: 'status',
      headerName: 'Status',
      width: 110,
      renderCell: (p) => <Chip size="small" label={p.value === 'ativo' ? 'Ativo' : 'Inativo'} color={p.value === 'ativo' ? 'success' : 'default'} />,
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 80,
      sortable: false,
      renderCell: (p) => (canEdit ? <IconButton size="small" onClick={() => { setEditing(p.row); setOpen(true); }}><EditIcon fontSize="small" /></IconButton> : null),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Prateleiras"
        subtitle="Cada prateleira pertence a um corredor"
        actionLabel={canCreate ? 'Nova prateleira' : undefined}
        onAction={canCreate ? () => { setEditing(null); setOpen(true); } : undefined}
      />
      <Box sx={{ height: 520 }}>
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
          <DialogTitle>{editing ? 'Editar' : 'Nova'} prateleira</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField label="Código" {...register('code')} error={!!errors.code} helperText={errors.code?.message} />
              <TextField label="Nome" {...register('name')} error={!!errors.name} helperText={errors.name?.message} />
              <Controller
                control={control}
                name="corridor_id"
                render={({ field }) => (
                  <TextField select label="Corredor" {...field} error={!!errors.corridor_id} helperText={errors.corridor_id?.message}>
                    <MenuItem value={0} disabled>Selecione...</MenuItem>
                    {corridors?.items.map((c) => (
                      <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                    ))}
                  </TextField>
                )}
              />
              <TextField label="Capacidade" type="number" {...register('capacity')} />
              <TextField label="Observações" multiline rows={2} {...register('observations')} />
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

export default function LocationsPage() {
  const [tab, setTab] = useState(0);
  return (
    <>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Corredores" />
        <Tab label="Prateleiras" />
      </Tabs>
      {tab === 0 ? (
        <CatalogCrud
          title="Corredores"
          subtitle="Cadastro de corredores do armazém"
          api={corridorsApi}
          queryKey="corridors"
          permission="corridor"
        />
      ) : (
        <ShelvesTab />
      )}
    </>
  );
}
