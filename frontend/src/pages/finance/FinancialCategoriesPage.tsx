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
import { financialCategoriesApi } from '@/api/endpoints';
import type { FinancialCategory, FinancialCategoryKind, Status } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import ConfirmDialog from '@/components/ConfirmDialog';
import PageHeader from '@/components/PageHeader';

export default function FinancialCategoriesPage() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<FinancialCategory | null>(null);
  const [name, setName] = useState('');
  const [kind, setKind] = useState<FinancialCategoryKind>('receita');
  const [status, setStatus] = useState<Status>('ativo');
  const [toDelete, setToDelete] = useState<FinancialCategory | null>(null);

  const canEdit = hasPermission('finance:create') || hasPermission('finance:update');
  const canDelete = hasPermission('finance:delete');

  const { data, isFetching } = useQuery({
    queryKey: ['financial-categories'],
    queryFn: () => financialCategoriesApi.list({ size: 200 }),
  });

  useEffect(() => {
    if (open) {
      setName(editing?.name ?? '');
      setKind(editing?.kind ?? 'receita');
      setStatus(editing?.status ?? 'ativo');
    }
  }, [open, editing]);

  const save = useMutation({
    mutationFn: () =>
      editing
        ? financialCategoriesApi.update(editing.id, { name, kind, status })
        : financialCategoriesApi.create({ name, kind, status }),
    onSuccess: () => {
      enqueueSnackbar('Categoria salva', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['financial-categories'] });
      setOpen(false);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const remove = useMutation({
    mutationFn: (id: number) => financialCategoriesApi.remove(id),
    onSuccess: () => {
      enqueueSnackbar('Categoria excluída', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['financial-categories'] });
      setToDelete(null);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<FinancialCategory>[] = [
    { field: 'name', headerName: 'Nome', flex: 1, minWidth: 200 },
    {
      field: 'kind',
      headerName: 'Tipo',
      width: 130,
      renderCell: (p) => (
        <Chip
          size="small"
          label={p.value === 'receita' ? 'Receita' : 'Despesa'}
          color={p.value === 'receita' ? 'success' : 'warning'}
          variant="outlined"
        />
      ),
    },
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
        title="Categorias Financeiras"
        subtitle="Receitas e despesas para classificação"
        actionLabel={canEdit ? 'Nova categoria' : undefined}
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
        <DialogTitle>{editing ? 'Editar' : 'Nova'} categoria</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Nome" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
            <TextField select label="Tipo" value={kind} onChange={(e) => setKind(e.target.value as FinancialCategoryKind)}>
              <MenuItem value="receita">Receita</MenuItem>
              <MenuItem value="despesa">Despesa</MenuItem>
            </TextField>
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
        title="Excluir categoria"
        message={`Deseja realmente excluir "${toDelete?.name}"?`}
        confirmLabel="Excluir"
        loading={remove.isPending}
        onClose={() => setToDelete(null)}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </Box>
  );
}
