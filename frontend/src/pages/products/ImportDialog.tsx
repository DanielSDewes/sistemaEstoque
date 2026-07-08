import UploadFileIcon from '@mui/icons-material/UploadFile';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Link,
  Typography,
} from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useRef, useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import { productExtrasApi } from '@/api/endpoints';
import type { ImportResult } from '@/api/types';

const TEMPLATE = 'internal_code,name,unit,barcode,sku,min_stock,max_stock,reorder_point\n';

export default function ImportDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const inputRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  const mutation = useMutation({
    mutationFn: (file: File) => productExtrasApi.importCsv(file),
    onSuccess: (res) => {
      setResult(res);
      qc.invalidateQueries({ queryKey: ['products'] });
      enqueueSnackbar(`Importação: ${res.created} criados, ${res.updated} atualizados`, {
        variant: res.errors.length ? 'warning' : 'success',
      });
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const downloadTemplate = () => {
    const url = URL.createObjectURL(new Blob([TEMPLATE], { type: 'text/csv' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'modelo_produtos.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Importar produtos (CSV)</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Envie um CSV com cabeçalho. Produtos existentes (mesmo <strong>internal_code</strong>) são
          atualizados. <Link component="button" onClick={downloadTemplate}>Baixar modelo</Link>.
        </Typography>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) mutation.mutate(file);
          }}
        />
        <Box sx={{ my: 2 }}>
          <Button
            variant="outlined"
            startIcon={<UploadFileIcon />}
            onClick={() => inputRef.current?.click()}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? 'Enviando...' : 'Selecionar arquivo CSV'}
          </Button>
        </Box>

        {result && (
          <Alert severity={result.errors.length ? 'warning' : 'success'}>
            {result.created} criados · {result.updated} atualizados
            {result.errors.length > 0 && (
              <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
                {result.errors.slice(0, 10).map((err, i) => (
                  <li key={i}>
                    Linha {err.line}: {err.error}
                  </li>
                ))}
              </Box>
            )}
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Fechar</Button>
      </DialogActions>
    </Dialog>
  );
}
