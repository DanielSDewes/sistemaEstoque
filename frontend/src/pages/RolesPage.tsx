import EditIcon from '@mui/icons-material/Edit';
import {
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  IconButton,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useMemo, useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import { permissionsApi, rolesApi, rolesExtraApi } from '@/api/endpoints';
import type { Permission, Role } from '@/api/types';
import PageHeader from '@/components/PageHeader';
import { useAuth } from '@/auth/AuthContext';

const RESOURCE_LABELS: Record<string, string> = {
  product: 'Produtos',
  category: 'Categorias',
  group: 'Grupos',
  subgroup: 'Subgrupos',
  brand: 'Marcas',
  corridor: 'Corredores',
  shelf: 'Prateleiras',
  supplier: 'Fornecedores',
  user: 'Usuários',
  role: 'Perfis',
  movement: 'Movimentações',
  inventory: 'Inventário',
  audit: 'Auditoria',
  dashboard: 'Dashboard',
  report: 'Relatórios',
};

function RoleEditor({
  role,
  permissions,
  onClose,
}: {
  role: Role | null;
  permissions: Permission[];
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const [name, setName] = useState(role?.name ?? '');
  const [description, setDescription] = useState(role?.description ?? '');
  const [selected, setSelected] = useState<Set<number>>(
    new Set(role?.permissions.map((p) => p.id) ?? []),
  );

  const grouped = useMemo(() => {
    const map: Record<string, Permission[]> = {};
    for (const p of permissions) {
      const resource = p.code.split(':')[0];
      (map[resource] ??= []).push(p);
    }
    return map;
  }, [permissions]);

  const toggle = (id: number) =>
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const save = useMutation({
    mutationFn: () => {
      const payload = { name, description, permission_ids: [...selected] };
      return role ? rolesExtraApi.update(role.id, payload) : rolesExtraApi.create(payload);
    },
    onSuccess: () => {
      enqueueSnackbar('Perfil salvo', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['roles'] });
      onClose();
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  return (
    <Dialog open onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{role ? `Editar perfil: ${role.name}` : 'Novo perfil'}</DialogTitle>
      <DialogContent dividers>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
          <TextField label="Nome" value={name} onChange={(e) => setName(e.target.value)} fullWidth
            disabled={role?.is_system} />
          <TextField label="Descrição" value={description} onChange={(e) => setDescription(e.target.value)} fullWidth />
        </Stack>
        {Object.entries(grouped).map(([resource, perms]) => (
          <Box key={resource} sx={{ mb: 1.5 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              {RESOURCE_LABELS[resource] ?? resource}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {perms.map((p) => (
                <FormControlLabel
                  key={p.id}
                  control={<Checkbox size="small" checked={selected.has(p.id)} onChange={() => toggle(p.id)} />}
                  label={<Typography variant="body2">{p.description}</Typography>}
                  sx={{ width: 260 }}
                />
              ))}
            </Box>
            <Divider sx={{ mt: 1 }} />
          </Box>
        ))}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button variant="contained" disabled={!name || save.isPending} onClick={() => save.mutate()}>
          Salvar
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default function RolesPage() {
  const { hasPermission } = useAuth();
  const [editing, setEditing] = useState<Role | null>(null);
  const [creating, setCreating] = useState(false);

  const canManage = hasPermission('role:update') || hasPermission('role:create');
  const { data: roles, isFetching } = useQuery({ queryKey: ['roles'], queryFn: () => rolesApi.list({ size: 100 }) });
  const { data: permissions } = useQuery({ queryKey: ['permissions'], queryFn: () => permissionsApi.list() });

  const columns: GridColDef<Role>[] = [
    { field: 'name', headerName: 'Perfil', width: 180 },
    { field: 'description', headerName: 'Descrição', flex: 1, minWidth: 200 },
    {
      field: 'permissions',
      headerName: 'Permissões',
      width: 130,
      valueGetter: (_v, row) => row.permissions.length,
      renderCell: (p) => <Chip size="small" label={`${p.value} permissões`} />,
    },
    {
      field: 'is_system',
      headerName: 'Sistema',
      width: 100,
      renderCell: (p) => (p.value ? <Chip size="small" label="Sistema" /> : null),
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 80,
      sortable: false,
      renderCell: (p) =>
        canManage ? (
          <IconButton size="small" onClick={() => setEditing(p.row)}>
            <EditIcon fontSize="small" />
          </IconButton>
        ) : null,
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Perfis e Permissões"
        subtitle="Defina o que cada perfil pode visualizar, inserir, alterar, excluir e aprovar"
        actionLabel={hasPermission('role:create') ? 'Novo perfil' : undefined}
        onAction={hasPermission('role:create') ? () => setCreating(true) : undefined}
      />
      <Paper sx={{ height: 520 }}>
        <DataGrid
          rows={roles?.items ?? []}
          columns={columns}
          loading={isFetching}
          disableColumnMenu
          disableRowSelectionOnClick
        />
      </Paper>
      {(editing || creating) && permissions && (
        <RoleEditor
          role={editing}
          permissions={permissions}
          onClose={() => {
            setEditing(null);
            setCreating(false);
          }}
        />
      )}
    </Box>
  );
}
