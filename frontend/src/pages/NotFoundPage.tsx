import { Box, Button, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <Box sx={{ textAlign: 'center', mt: 8 }}>
      <Typography variant="h3" fontWeight={800} color="primary">
        404
      </Typography>
      <Typography variant="h6" gutterBottom>
        Página não encontrada
      </Typography>
      <Button variant="contained" onClick={() => navigate('/')} sx={{ mt: 2 }}>
        Voltar ao início
      </Button>
    </Box>
  );
}
