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
  TextField,
} from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useEffect, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiErrorMessage } from '@/api/client';
import { rolesApi, usersApi } from '@/api/endpoints';
import { api } from '@/api/client';
import type { User } from '@/api/types';
import PageHeader from '@/components/PageHeader';
import { useAuth } from '@/auth/AuthContext';
import { passwordSchema } from '@/utils/password';

const schema = z.object({
  full_name: z.string().min(2, 'Obrigatório'),
  email: z.string().email('E-mail inválido'),
  username: z.string().min(3, 'Mínimo 3 caracteres'),
  password: z
    .string()
    .optional()
    .refine((v) => !v || passwordSchema.safeParse(v).success, {
      message: 'Mín. 8 caracteres com maiúscula, minúscula, número e símbolo',
    }),
  role_id: z.coerce.number().min(1, 'Selecione um perfil'),
  is_active: z.boolean(),
});
type FormData = z.infer<typeof schema>;

const EMPTY: FormData = { full_name: '', email: '', username: '', password: '', role_id: 0, is_active: true };

export default function UsersPage() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);

  const canCreate = hasPermission('user:create');
  const canEdit = hasPermission('user:update');

  const { data, isFetching } = useQuery({
    queryKey: ['users', page, pageSize],
    queryFn: () => usersApi.list({ page: page + 1, size: pageSize }),
  });
  const { data: roles } = useQuery({ queryKey: ['roles', 'all'], queryFn: () => rolesApi.list({ size: 100 }) });

  const { register, handleSubmit, reset, control, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  });

  useEffect(() => {
    reset(
      editing
        ? {
            full_name: editing.full_name,
            email: editing.email,
            username: editing.username,
            password: '',
            role_id: editing.role.id,
            is_active: editing.is_active,
          }
        : EMPTY,
    );
  }, [editing, reset]);

  const mutation = useMutation({
    mutationFn: async (values: FormData) => {
      if (editing) {
        return usersApi.update(editing.id, {
          full_name: values.full_name,
          email: values.email,
          role_id: values.role_id,
          is_active: values.is_active,
        } as Partial<User>);
      }
      // Create goes through the raw client to include the password field.
      const { data: created } = await api.post<User>('/users', values);
      return created;
    },
    onSuccess: () => {
      enqueueSnackbar('Usuário salvo', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['users'] });
      setOpen(false);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<User>[] = [
    { field: 'full_name', headerName: 'Nome', flex: 1, minWidth: 180 },
    { field: 'username', headerName: 'Usuário', width: 140 },
    { field: 'email', headerName: 'E-mail', flex: 1, minWidth: 180 },
    { field: 'role', headerName: 'Perfil', width: 160, valueGetter: (_v, row) => row.role?.name },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 110,
      renderCell: (p) => (
        <Chip size="small" label={p.value ? 'Ativo' : 'Inativo'} color={p.value ? 'success' : 'default'} />
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
        title="Usuários e Perfis"
        subtitle="Controle de acesso por perfil (RBAC)"
        actionLabel={canCreate ? 'Novo usuário' : undefined}
        onAction={canCreate ? () => { setEditing(null); setOpen(true); } : undefined}
      />
      <Box sx={{ height: 560 }}>
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
          <DialogTitle>{editing ? 'Editar' : 'Novo'} usuário</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField label="Nome completo" {...register('full_name')} error={!!errors.full_name} helperText={errors.full_name?.message} />
              <TextField label="E-mail" {...register('email')} error={!!errors.email} helperText={errors.email?.message} />
              <TextField
                label="Usuário"
                {...register('username')}
                disabled={!!editing}
                error={!!errors.username}
                helperText={errors.username?.message}
              />
              {!editing && (
                <TextField label="Senha" type="password" {...register('password')} error={!!errors.password} helperText={errors.password?.message} />
              )}
              <Controller
                control={control}
                name="role_id"
                render={({ field }) => (
                  <TextField select label="Perfil" {...field} error={!!errors.role_id} helperText={errors.role_id?.message}>
                    <MenuItem value={0} disabled>
                      Selecione...
                    </MenuItem>
                    {roles?.items.map((r) => (
                      <MenuItem key={r.id} value={r.id}>
                        {r.name}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
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
