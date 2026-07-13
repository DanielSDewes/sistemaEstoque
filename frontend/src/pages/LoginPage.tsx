import { zodResolver } from '@hookform/resolvers/zod';
import Warehouse from '@mui/icons-material/Warehouse';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link as RouterLink, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { apiErrorMessage } from '@/api/client';
import { useAuth } from '@/auth/AuthContext';

const schema = z.object({
  username: z.string().min(1, 'Informe o usuário ou e-mail'),
  password: z.string().min(1, 'Informe a senha'),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);
  const resetOk = (location.state as { resetOk?: boolean } | null)?.resetOk;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { username: '', password: '' },
  });

  if (user) {
    const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/';
    return <Navigate to={from} replace />;
  }

  const onSubmit = async (data: FormData) => {
    setError(null);
    try {
      await login(data.username, data.password);
      navigate('/', { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, 'Falha na autenticação'));
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        background: 'linear-gradient(135deg, #1F4E78 0%, #143654 100%)',
      }}
    >
      <Card sx={{ width: '100%', maxWidth: 420, borderRadius: 3, boxShadow: 6 }}>
        <CardContent sx={{ p: 4 }}>
          <Stack alignItems="center" spacing={1} sx={{ mb: 3 }}>
            <Warehouse color="primary" sx={{ fontSize: 48 }} />
            <Typography variant="h5" align="center">
              Sistema de Estoque
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Acesse com suas credenciais
            </Typography>
          </Stack>

          {resetOk && !error && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Senha redefinida com sucesso. Entre com a nova senha.
            </Alert>
          )}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
            <Stack spacing={2}>
              <TextField
                label="Usuário ou e-mail"
                fullWidth
                autoFocus
                autoComplete="username"
                {...register('username')}
                error={!!errors.username}
                helperText={errors.username?.message}
              />
              <TextField
                label="Senha"
                type="password"
                fullWidth
                autoComplete="current-password"
                {...register('password')}
                error={!!errors.password}
                helperText={errors.password?.message}
              />
              <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
                {isSubmitting ? 'Entrando...' : 'Entrar'}
              </Button>
            </Stack>
          </Box>

          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography
              component={RouterLink}
              to="/forgot-password"
              variant="body2"
              color="primary"
              sx={{ textDecoration: 'none' }}
            >
              Esqueci minha senha
            </Typography>
          </Box>

          <Typography
            variant="caption"
            color="text.secondary"
            align="center"
            display="block"
            sx={{ mt: 3 }}
          >
            Padrão: admin / Admin@123
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
