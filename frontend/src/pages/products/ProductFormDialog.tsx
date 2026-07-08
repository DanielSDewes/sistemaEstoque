import { zodResolver } from '@hookform/resolvers/zod';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import {
  Avatar,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useEffect, useRef } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';

import { apiErrorMessage, assetUrl } from '@/api/client';
import { brandsApi, categoriesApi, groupsApi, productExtrasApi, productsApi } from '@/api/endpoints';
import type { Product } from '@/api/types';

const schema = z.object({
  internal_code: z.string().min(1, 'Obrigatório').max(40),
  name: z.string().min(1, 'Obrigatório').max(200),
  barcode: z.string().max(60).optional().or(z.literal('')),
  sku: z.string().max(60).optional().or(z.literal('')),
  short_name: z.string().max(80).optional().or(z.literal('')),
  description: z.string().optional().or(z.literal('')),
  unit: z.string().max(20),
  category_id: z.coerce.number().optional().nullable(),
  group_id: z.coerce.number().optional().nullable(),
  brand_id: z.coerce.number().optional().nullable(),
  min_stock: z.coerce.number().min(0),
  max_stock: z.coerce.number().min(0),
  reorder_point: z.coerce.number().min(0),
  sale_price: z.coerce.number().min(0),
  is_active: z.boolean(),
});
type FormData = z.infer<typeof schema>;

const EMPTY: FormData = {
  internal_code: '',
  name: '',
  barcode: '',
  sku: '',
  short_name: '',
  description: '',
  unit: 'UN',
  category_id: null,
  group_id: null,
  brand_id: null,
  min_stock: 0,
  max_stock: 0,
  reorder_point: 0,
  sale_price: 0,
  is_active: true,
};

const money = (n: number | null | undefined) =>
  n == null ? '—' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

interface Props {
  open: boolean;
  product: Product | null;
  onClose: () => void;
}

export default function ProductFormDialog({ open, product, onClose }: Props) {
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();

  const { data: categories } = useQuery({ queryKey: ['categories', 'all'], queryFn: () => categoriesApi.list({ size: 200 }) });
  const { data: groups } = useQuery({ queryKey: ['groups', 'all'], queryFn: () => groupsApi.list({ size: 200 }) });
  const { data: brands } = useQuery({ queryKey: ['brands', 'all'], queryFn: () => brandsApi.list({ size: 200 }) });

  const { register, handleSubmit, reset, control, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  });

  useEffect(() => {
    if (product) {
      reset({
        internal_code: product.internal_code,
        name: product.name,
        barcode: product.barcode ?? '',
        sku: product.sku ?? '',
        short_name: product.short_name ?? '',
        description: product.description ?? '',
        unit: product.unit,
        category_id: product.category?.id ?? null,
        group_id: product.group?.id ?? null,
        brand_id: product.brand?.id ?? null,
        min_stock: product.min_stock,
        max_stock: product.max_stock,
        reorder_point: product.reorder_point,
        sale_price: product.sale_price,
        is_active: product.is_active,
      });
    } else {
      reset(EMPTY);
    }
  }, [product, reset]);

  const mutation = useMutation({
    mutationFn: (values: FormData) => {
      const payload = {
        ...values,
        category_id: values.category_id || null,
        group_id: values.group_id || null,
        brand_id: values.brand_id || null,
      };
      return product ? productsApi.update(product.id, payload) : productsApi.create(payload);
    },
    onSuccess: () => {
      enqueueSnackbar(product ? 'Produto atualizado' : 'Produto criado', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['products'] });
      onClose();
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const photoInput = useRef<HTMLInputElement>(null);
  const photoMutation = useMutation({
    mutationFn: (file: File) => productExtrasApi.uploadPhoto(product!.id, file),
    onSuccess: () => {
      enqueueSnackbar('Foto atualizada', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit((v) => mutation.mutate(v))}>
        <DialogTitle>{product ? 'Editar produto' : 'Novo produto'}</DialogTitle>
        <DialogContent dividers>
          {product && (
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
              <Avatar src={assetUrl(product.photo_url)} variant="rounded" sx={{ width: 64, height: 64 }}>
                {product.name[0]}
              </Avatar>
              <input
                ref={photoInput}
                type="file"
                accept="image/*"
                hidden
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) photoMutation.mutate(file);
                }}
              />
              <Button
                size="small"
                variant="outlined"
                startIcon={<PhotoCameraIcon />}
                onClick={() => photoInput.current?.click()}
                disabled={photoMutation.isPending}
              >
                {photoMutation.isPending ? 'Enviando...' : 'Enviar foto'}
              </Button>
            </Stack>
          )}
          <Typography variant="overline" color="text.secondary">
            Identificação
          </Typography>
          <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, mb: 2 }}>
            <TextField
              label="Código interno"
              {...register('internal_code')}
              error={!!errors.internal_code}
              helperText={errors.internal_code?.message}
            />
            <TextField label="Código de barras" {...register('barcode')} />
            <TextField label="SKU" {...register('sku')} />
            <TextField
              label="Nome"
              {...register('name')}
              error={!!errors.name}
              helperText={errors.name?.message}
            />
            <TextField label="Nome reduzido" {...register('short_name')} />
            <TextField label="Unidade" {...register('unit')} />
          </Box>
          <TextField label="Descrição" fullWidth multiline rows={2} {...register('description')} sx={{ mb: 2 }} />

          <Divider sx={{ my: 1 }} />
          <Typography variant="overline" color="text.secondary">
            Classificação
          </Typography>
          <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, mb: 2 }}>
            <Controller
              control={control}
              name="category_id"
              render={({ field }) => (
                <TextField select label="Categoria" {...field} value={field.value ?? ''}>
                  <MenuItem value="">—</MenuItem>
                  {categories?.items.map((c) => (
                    <MenuItem key={c.id} value={c.id}>
                      {c.name}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
            <Controller
              control={control}
              name="group_id"
              render={({ field }) => (
                <TextField select label="Grupo" {...field} value={field.value ?? ''}>
                  <MenuItem value="">—</MenuItem>
                  {groups?.items.map((g) => (
                    <MenuItem key={g.id} value={g.id}>
                      {g.name}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
            <Controller
              control={control}
              name="brand_id"
              render={({ field }) => (
                <TextField select label="Marca" {...field} value={field.value ?? ''}>
                  <MenuItem value="">—</MenuItem>
                  {brands?.items.map((b) => (
                    <MenuItem key={b.id} value={b.id}>
                      {b.name}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Box>

          <Divider sx={{ my: 1 }} />
          <Typography variant="overline" color="text.secondary">
            Preços
          </Typography>
          <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, mb: 2 }}>
            <TextField
              label="Preço de venda"
              type="number"
              inputProps={{ min: 0, step: '0.01' }}
              {...register('sale_price')}
              error={!!errors.sale_price}
              helperText={errors.sale_price?.message ?? 'Sugerido como padrão nos pedidos'}
            />
            <TextField
              label="Custo médio"
              value={money(product?.average_cost)}
              InputProps={{ readOnly: true }}
              helperText="Atualizado automaticamente pelas compras"
            />
          </Box>

          <Divider sx={{ my: 1 }} />
          <Typography variant="overline" color="text.secondary">
            Configuração de estoque
          </Typography>
          <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' } }}>
            <TextField label="Estoque mínimo" type="number" {...register('min_stock')} />
            <TextField label="Estoque máximo" type="number" {...register('max_stock')} />
            <TextField label="Ponto de reposição" type="number" {...register('reorder_point')} />
          </Box>

          <Controller
            control={control}
            name="is_active"
            render={({ field }) => (
              <FormControlLabel
                sx={{ mt: 1 }}
                control={<Switch checked={field.value} onChange={(e) => field.onChange(e.target.checked)} />}
                label="Produto ativo"
              />
            )}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancelar</Button>
          <Button type="submit" variant="contained" disabled={mutation.isPending}>
            Salvar
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
