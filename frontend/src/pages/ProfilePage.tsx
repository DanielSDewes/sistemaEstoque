import { zodResolver } from '@hookform/resolvers/zod';
import { Avatar, Box, Button, Card, CardContent, Divider, Stack, TextField, Typography } from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiErrorMessage } from '@/api/client';
import { accountApi } from '@/api/endpoints';
import { useAuth } from '@/auth/AuthContext';
import PageHeader from '@/components/PageHeader';
import { passwordSchema } from '@/utils/password';

const schema = z
  .object({
    current_password: z.string().min(1, 'Informe a senha atual'),
    new_password: passwordSchema,
    confirm: z.string(),
  })
  .refine((d) => d.new_password === d.confirm, {
    message: 'As senhas não coincidem',
    path: ['confirm'],
  });
type FormData = z.infer<typeof schema>;

export default function ProfilePage() {
  const { user } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { current_password: '', new_password: '', confirm: '' },
  });

  const mutation = useMutation({
    mutationFn: (d: FormData) => accountApi.changePassword(d.current_password, d.new_password),
    onSuccess: () => {
      enqueueSnackbar('Senha alterada com sucesso', { variant: 'success' });
      reset();
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  return (
    <Box>
      <PageHeader title="Meu Perfil" subtitle="Dados da conta e segurança" />
      <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' } }}>
        <Card>
          <CardContent>
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
              <Avatar sx={{ width: 56, height: 56, bgcolor: 'primary.main' }}>
                {user?.full_name?.[0]}
              </Avatar>
              <Box>
                <Typography variant="h6">{user?.full_name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {user?.email} · {user?.role?.name}
                </Typography>
              </Box>
            </Stack>
            <Divider />
            <Stack spacing={0.5} sx={{ mt: 2 }}>
              <Typography variant="body2"><strong>Usuário:</strong> {user?.username}</Typography>
              <Typography variant="body2"><strong>Perfil:</strong> {user?.role?.name}</Typography>
              <Typography variant="body2">
                <strong>Permissões:</strong> {user?.is_superuser ? 'Todas (superusuário)' : user?.role?.permissions?.length}
              </Typography>
            </Stack>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={700} gutterBottom>
              Alterar senha
            </Typography>
            <Box component="form" onSubmit={handleSubmit((d) => mutation.mutate(d))}>
              <Stack spacing={2}>
                <TextField label="Senha atual" type="password" {...register('current_password')}
                  error={!!errors.current_password} helperText={errors.current_password?.message} />
                <TextField label="Nova senha" type="password" {...register('new_password')}
                  error={!!errors.new_password} helperText={errors.new_password?.message} />
                <TextField label="Confirmar nova senha" type="password" {...register('confirm')}
                  error={!!errors.confirm} helperText={errors.confirm?.message} />
                <Button type="submit" variant="contained" disabled={mutation.isPending}>
                  Alterar senha
                </Button>
              </Stack>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}
