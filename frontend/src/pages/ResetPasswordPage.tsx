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
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom';

import { apiErrorMessage } from '@/api/client';
import { authApi } from '@/api/endpoints';
import { passwordSchema } from '@/utils/password';

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const pwdError = password.length > 0 ? passwordSchema.safeParse(password).error?.issues[0]?.message : undefined;
  const mismatch = confirm.length > 0 && confirm !== password;
  const canSubmit = !!token && !pwdError && !mismatch && password.length > 0 && confirm.length > 0;

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authApi.resetPassword(token, password);
      navigate('/login', {
        replace: true,
        state: { resetOk: true },
      });
    } catch (err) {
      setError(apiErrorMessage(err, 'Não foi possível redefinir a senha'));
    } finally {
      setLoading(false);
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
              Nova senha
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Defina uma nova senha para sua conta
            </Typography>
          </Stack>

          {!token && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Link inválido: token de redefinição ausente.
            </Alert>
          )}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={onSubmit} noValidate>
            <Stack spacing={2}>
              <TextField
                label="Nova senha"
                type="password"
                fullWidth
                autoFocus
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={!!pwdError}
                helperText={pwdError ?? 'Mínimo 8 caracteres, com maiúscula, minúscula, número e símbolo'}
              />
              <TextField
                label="Confirmar senha"
                type="password"
                fullWidth
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                error={mismatch}
                helperText={mismatch ? 'As senhas não coincidem' : ' '}
              />
              <Button type="submit" variant="contained" size="large" disabled={!canSubmit || loading}>
                {loading ? 'Salvando...' : 'Redefinir senha'}
              </Button>
              <Button component={RouterLink} to="/login" size="small">
                Voltar ao login
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
