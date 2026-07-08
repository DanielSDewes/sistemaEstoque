import { zodResolver } from '@hookform/resolvers/zod';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiErrorMessage } from '@/api/client';
import { movementsApi } from '@/api/endpoints';
import type { Product } from '@/api/types';

const IN_TYPES = [
  { value: 'compra', label: 'Compra' },
  { value: 'ajuste_entrada', label: 'Ajuste (entrada)' },
  { value: 'devolucao', label: 'Devolução' },
  { value: 'producao', label: 'Produção' },
];
const OUT_TYPES = [
  { value: 'venda', label: 'Venda' },
  { value: 'consumo_interno', label: 'Consumo interno' },
  { value: 'perda', label: 'Perda' },
  { value: 'quebra', label: 'Quebra' },
  { value: 'ajuste_saida', label: 'Ajuste (saída)' },
];

const schema = z.object({
  movement_type: z.string().min(1),
  quantity: z.coerce.number().positive('Quantidade deve ser maior que zero'),
  unit_cost: z.coerce.number().min(0).optional(),
  document: z.string().max(80).optional().or(z.literal('')),
  reason: z.string().max(200).optional().or(z.literal('')),
});
type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  product: Product | null;
  onClose: () => void;
}

export default function MovementDialog({ open, product, onClose }: Props) {
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();

  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { movement_type: 'compra', quantity: 1, unit_cost: undefined, document: '', reason: '' },
  });

  const mutation = useMutation({
    mutationFn: (values: FormData) =>
      movementsApi.create({ product_id: product!.id, ...values }),
    onSuccess: () => {
      enqueueSnackbar('Movimentação registrada', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['products'] });
      qc.invalidateQueries({ queryKey: ['movements'] });
      reset();
      onClose();
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <form onSubmit={handleSubmit((v) => mutation.mutate(v))}>
        <DialogTitle>Movimentar estoque</DialogTitle>
        <DialogContent>
          {product && (
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {product.internal_code} — {product.name}
              {product.stock && ` · Saldo atual: ${product.stock.current}`}
            </Typography>
          )}
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Controller
              control={control}
              name="movement_type"
              render={({ field }) => (
                <TextField select label="Tipo" {...field}>
                  <MenuItem disabled>— Entradas —</MenuItem>
                  {IN_TYPES.map((t) => (
                    <MenuItem key={t.value} value={t.value}>
                      {t.label}
                    </MenuItem>
                  ))}
                  <MenuItem disabled>— Saídas —</MenuItem>
                  {OUT_TYPES.map((t) => (
                    <MenuItem key={t.value} value={t.value}>
                      {t.label}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
            <TextField
              label="Quantidade"
              type="number"
              inputProps={{ step: 'any' }}
              {...register('quantity')}
              error={!!errors.quantity}
              helperText={errors.quantity?.message}
            />
            <TextField label="Custo unitário (opcional)" type="number" inputProps={{ step: 'any' }} {...register('unit_cost')} />
            <TextField label="Documento" {...register('document')} />
            <TextField label="Motivo / observação" {...register('reason')} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancelar</Button>
          <Button type="submit" variant="contained" disabled={mutation.isPending}>
            Registrar
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
