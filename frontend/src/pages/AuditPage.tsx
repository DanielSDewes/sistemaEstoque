import { Box, Chip } from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { auditApi } from '@/api/endpoints';
import type { AuditLog } from '@/api/types';
import PageHeader from '@/components/PageHeader';

const ACTION_COLORS: Record<string, 'success' | 'info' | 'error' | 'warning' | 'default'> = {
  inclusao: 'success',
  alteracao: 'info',
  exclusao: 'error',
  login: 'default',
  logout: 'default',
  movimentacao: 'warning',
  aprovacao: 'success',
  cancelamento: 'error',
};

export default function AuditPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);

  const { data, isFetching } = useQuery({
    queryKey: ['audit', page, pageSize],
    queryFn: () => auditApi.list({ page: page + 1, size: pageSize }),
  });

  const columns: GridColDef<AuditLog>[] = [
    {
      field: 'created_at',
      headerName: 'Data/Hora',
      width: 170,
      valueGetter: (v) => new Date(v as string).toLocaleString('pt-BR'),
    },
    { field: 'username', headerName: 'Usuário', width: 140 },
    {
      field: 'action',
      headerName: 'Ação',
      width: 140,
      renderCell: (p) => (
        <Chip size="small" label={p.value} color={ACTION_COLORS[p.value as string] ?? 'default'} />
      ),
    },
    { field: 'entity', headerName: 'Entidade', width: 140 },
    { field: 'entity_id', headerName: 'ID', width: 80 },
    { field: 'field', headerName: 'Campo', width: 130 },
    { field: 'old_value', headerName: 'Valor anterior', flex: 1, minWidth: 130 },
    { field: 'new_value', headerName: 'Valor novo', flex: 1, minWidth: 130 },
    { field: 'ip_address', headerName: 'IP', width: 130 },
  ];

  return (
    <Box>
      <PageHeader
        title="Auditoria"
        subtitle="Registro imutável de todas as ações. Nada pode ser excluído da auditoria."
      />
      <Box sx={{ height: 640 }}>
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
          sx={{ bgcolor: 'background.paper' }}
        />
      </Box>
    </Box>
  );
}
