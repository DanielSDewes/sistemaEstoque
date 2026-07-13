import Warehouse from '@mui/icons-material/Warehouse';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Link,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';

import { apiErrorMessage } from '@/api/client';
import { authApi } from '@/api/endpoints';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.forgotPassword(email.trim());
      setSent(true);
      // Outside production the API returns the token so the flow is testable
      // without a mail server (shown as a direct link below).
      setDevToken(res.reset_token);
    } catch (err) {
      setError(apiErrorMessage(err, 'Não foi possível processar a solicitação'));
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
              Redefinir senha
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Informe seu e-mail para receber o link de redefinição
            </Typography>
          </Stack>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {sent ? (
            <Stack spacing={2}>
              <Alert severity="success">
                Se o e-mail existir, um link de redefinição foi enviado.
              </Alert>
              {devToken && (
                <Alert severity="info">
                  Ambiente de demonstração (sem servidor de e-mail): use o link abaixo.
                  <Box sx={{ mt: 1 }}>
                    <Link component={RouterLink} to={`/reset-password?token=${devToken}`}>
                      Abrir página de redefinição
                    </Link>
                  </Box>
                </Alert>
              )}
              <Button component={RouterLink} to="/login" variant="outlined">
                Voltar ao login
              </Button>
            </Stack>
          ) : (
            <Box component="form" onSubmit={onSubmit} noValidate>
              <Stack spacing={2}>
                <TextField
                  label="E-mail"
                  type="email"
                  fullWidth
                  autoFocus
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  disabled={loading || email.trim().length === 0}
                >
                  {loading ? 'Enviando...' : 'Enviar link'}
                </Button>
                <Button component={RouterLink} to="/login" size="small">
                  Voltar ao login
                </Button>
              </Stack>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
