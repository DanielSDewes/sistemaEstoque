import CancelIcon from '@mui/icons-material/Cancel';
import { Box, Chip, IconButton, Tooltip } from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { useState } from 'react';

import { apiErrorMessage } from '@/api/client';
import { movementsApi } from '@/api/endpoints';
import type { Movement } from '@/api/types';
import PageHeader from '@/components/PageHeader';
import ConfirmDialog from '@/components/ConfirmDialog';
import { useAuth } from '@/auth/AuthContext';

const TYPE_LABELS: Record<string, string> = {
  compra: 'Compra',
  ajuste_entrada: 'Ajuste entrada',
  devolucao: 'Devolução',
  producao: 'Produção',
  venda: 'Venda',
  consumo_interno: 'Consumo interno',
  perda: 'Perda',
  quebra: 'Quebra',
  transferencia: 'Transferência',
  ajuste_saida: 'Ajuste saída',
};

export default function MovementsPage() {
  const { hasPermission } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [toCancel, setToCancel] = useState<Movement | null>(null);

  const canCancel = hasPermission('movement:cancel');

  const { data, isFetching } = useQuery({
    queryKey: ['movements', page, pageSize],
    queryFn: () => movementsApi.list({ page: page + 1, size: pageSize }),
  });

  const cancelMutation = useMutation({
    mutationFn: (m: Movement) => movementsApi.cancel(m.id, 'Cancelada via painel'),
    onSuccess: () => {
      enqueueSnackbar('Movimentação cancelada', { variant: 'success' });
      qc.invalidateQueries({ queryKey: ['movements'] });
      qc.invalidateQueries({ queryKey: ['products'] });
      setToCancel(null);
    },
    onError: (e) => enqueueSnackbar(apiErrorMessage(e), { variant: 'error' }),
  });

  const columns: GridColDef<Movement>[] = [
    { field: 'id', headerName: '#', width: 70 },
    {
      field: 'moved_at',
      headerName: 'Data/Hora',
      width: 170,
      valueGetter: (v) => new Date(v as string).toLocaleString('pt-BR'),
    },
    { field: 'product_id', headerName: 'Produto', width: 90 },
    {
      field: 'movement_type',
      headerName: 'Tipo',
      width: 150,
      valueGetter: (v) => TYPE_LABELS[v as string] ?? v,
    },
    {
      field: 'direction',
      headerName: 'Direção',
      width: 110,
      renderCell: (p) => (
        <Chip
          size="small"
          label={p.value === 'entrada' ? 'Entrada' : 'Saída'}
          color={p.value === 'entrada' ? 'success' : 'error'}
          variant="outlined"
        />
      ),
    },
    { field: 'quantity', headerName: 'Qtd', width: 90 },
    {
      field: 'is_cancelled',
      headerName: 'Situação',
      width: 120,
      renderCell: (p) =>
        p.value ? (
          <Chip size="small" label="Cancelada" color="default" />
        ) : (
          <Chip size="small" label="Ativa" color="primary" variant="outlined" />
        ),
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 90,
      sortable: false,
      renderCell: (p) =>
        canCancel && !p.row.is_cancelled ? (
          <Tooltip title="Cancelar">
            <IconButton size="small" color="error" onClick={() => setToCancel(p.row)}>
              <CancelIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        ) : null,
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Movimentações"
        subtitle="Histórico de entradas e saídas. Movimentações nunca são apagadas, apenas canceladas."
      />
      <Box sx={{ height: 620 }}>
        <DataGrid
          rows={data?.items ?? []}
          columns={columns}
          loading={isFetching}
          rowCount={data?.total ?? 0}
          paginationMode="server"
          paginationModel={{ page, pageSize }}
          onPaginationModelChange={(m) => {
            setPage(m.page);
            setPageSize(m.pageSize);
          }}
          pageSizeOptions={[20, 50, 100]}
          disableColumnMenu
          disableRowSelectionOnClick
          getRowClassName={(p) => (p.row.is_cancelled ? 'cancelled-row' : '')}
          sx={{
            bgcolor: 'background.paper',
            '& .cancelled-row': { opacity: 0.55, textDecoration: 'line-through' },
          }}
        />
      </Box>

      <ConfirmDialog
        open={!!toCancel}
        title="Cancelar movimentação"
        message={`Cancelar a movimentação #${toCancel?.id}? O saldo será revertido e o histórico mantido.`}
        confirmLabel="Cancelar movimentação"
        loading={cancelMutation.isPending}
        onClose={() => setToCancel(null)}
        onConfirm={() => toCancel && cancelMutation.mutate(toCancel)}
      />
    </Box>
  );
}
