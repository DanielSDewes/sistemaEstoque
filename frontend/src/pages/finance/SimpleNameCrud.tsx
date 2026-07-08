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
import { useEffect, useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import type { createCrudApi } from '@/api/crud';
import type { Status } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import ConfirmDialog from '@/components/ConfirmDialog';
import PageHeader from '@/components/PageHeader';

interface NamedItem {
  id: number;
  name: string;
  status: Status;
}

interface Props {
  title: string;
  subtitle?: string;
  queryKey: string;
  api: ReturnType<typeof createCrudApi<NamedItem>>;
}

export default function SimpleNameCrud({ title, subtitle, queryKey, api }: Props) {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<NamedItem | null>(null);
  const [name, setName] = useState('');
  const [status, setStatus] = useState<Status>('ativo');
  const [toDelete, setToDelete] = useState<NamedItem | null>(null);

  const canEdit = hasPermission('finance:create') || hasPermission('finance:update');
  const canDelete = hasPermission('finance:delete');

  const { data, isFetching } = useQuery({
    queryKey: [queryKey],
    queryFn: () => api.list({ size: 200 }),
  });

  useEffect(() => {
    if (open) {
      setName(editing?.name ?? '');
      setStatus(editing?.status ?? 'ativo');
    }
  }, [open, editing]);

  const save = useMutation({
    mutationFn: () =>
      editing ? api.update(editing.id, { name, status }) : api.create({ name, status }),
    onSuccess: () => {
      enqueueSnackbar('Registro salvo', { variant: 'success' });
      qc.invalidateQueries({ queryKey: [queryKey] });
      setOpen(false);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.remove(id),
    onSuccess: () => {
      enqueueSnackbar('Registro excluído', { variant: 'success' });
      qc.invalidateQueries({ queryKey: [queryKey] });
      setToDelete(null);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<NamedItem>[] = [
    { field: 'name', headerName: 'Nome', flex: 1, minWidth: 220 },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (p) => (
        <Chip size="small" label={p.value === 'ativo' ? 'Ativo' : 'Inativo'} color={p.value === 'ativo' ? 'success' : 'default'} />
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
            <IconButton size="small" onClick={() => { setEditing(p.row); setOpen(true); }}>
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
        onAction={canEdit ? () => { setEditing(null); setOpen(true); } : undefined}
      />
      <Box sx={{ height: 560 }}>
        <DataGrid
          rows={data?.items ?? []}
          columns={columns}
          loading={isFetching}
          pageSizeOptions={[10, 20, 50]}
          initialState={{ pagination: { paginationModel: { pageSize: 20 } } }}
          disableColumnMenu
          disableRowSelectionOnClick
          sx={{ bgcolor: 'background.paper' }}
        />
      </Box>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>{editing ? 'Editar' : 'Novo'} registro</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Nome" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
            <TextField select label="Status" value={status} onChange={(e) => setStatus(e.target.value as Status)}>
              <MenuItem value="ativo">Ativo</MenuItem>
              <MenuItem value="inativo">Inativo</MenuItem>
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancelar</Button>
          <Button variant="contained" disabled={!name.trim() || save.isPending} onClick={() => save.mutate()}>
            Salvar
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={!!toDelete}
        title="Excluir registro"
        message={`Deseja realmente excluir "${toDelete?.name}"?`}
        confirmLabel="Excluir"
        loading={remove.isPending}
        onClose={() => setToDelete(null)}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </Box>
  );
}
