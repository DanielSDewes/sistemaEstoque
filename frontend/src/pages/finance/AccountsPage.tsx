import VisibilityIcon from '@mui/icons-material/Visibility';
import { Box, Chip, IconButton, MenuItem, Stack, TextField } from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { financeApi } from '@/api/endpoints';
import type { FinancialAccount, FinancialDirection, FinancialStatus } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import PageHeader from '@/components/PageHeader';
import SearchBar from '@/components/SearchBar';
import AccountDetailDialog from '@/pages/finance/AccountDetailDialog';
import AccountFormDialog from '@/pages/finance/AccountFormDialog';
import { money, statusInfo } from '@/pages/finance/financeUtils';

interface Props {
  direction: FinancialDirection;
}

export default function AccountsPage({ direction }: Props) {
  const { hasPermission } = useAuth();
  const isReceivable = direction === 'receber';
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<FinancialStatus | ''>('');
  const [formOpen, setFormOpen] = useState(false);
  const [detailId, setDetailId] = useState<number | null>(null);

  const canCreate = hasPermission('finance:create');

  const { data, isFetching } = useQuery({
    queryKey: ['finance-accounts', direction, page, pageSize, search, status],
    queryFn: () =>
      financeApi.listAccounts({
        direction,
        page: page + 1,
        size: pageSize,
        q: search,
        status: status || undefined,
      }),
  });

  const columns: GridColDef<FinancialAccount>[] = [
    { field: 'document', headerName: 'Documento', width: 140 },
    {
      field: 'party_name',
      headerName: isReceivable ? 'Cliente' : 'Fornecedor',
      flex: 1,
      minWidth: 170,
      valueGetter: (v) => v ?? '—',
    },
    {
      field: 'total_amount',
      headerName: 'Valor',
      width: 120,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (v) => money(v as number),
    },
    {
      field: 'balance',
      headerName: 'Saldo',
      width: 120,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (v) => money(v as number),
    },
    {
      field: 'installments',
      headerName: 'Próx. venc.',
      width: 120,
      sortable: false,
      valueGetter: (_v, row) => {
        const open = row.installments.filter((i) => i.status === 'em_aberto' || i.status === 'parcial' || i.status === 'vencido');
        const next = open.map((i) => i.due_date).sort()[0];
        return next ? new Date(next).toLocaleDateString('pt-BR') : '—';
      },
    },
    {
      field: 'status',
      headerName: 'Situação',
      width: 130,
      renderCell: (p) => {
        const info = statusInfo(p.value as FinancialStatus, direction);
        return <Chip size="small" color={info.color} label={info.label} />;
      },
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 80,
      sortable: false,
      renderCell: (p) => (
        <IconButton size="small" onClick={() => setDetailId(p.row.id)} title="Detalhes / baixar">
          <VisibilityIcon fontSize="small" />
        </IconButton>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title={isReceivable ? 'Contas a Receber' : 'Contas a Pagar'}
        subtitle={isReceivable ? 'Direitos a receber dos clientes' : 'Obrigações a pagar aos fornecedores'}
        actionLabel={canCreate ? 'Nova conta' : undefined}
        onAction={canCreate ? () => setFormOpen(true) : undefined}
      />
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <SearchBar placeholder="Buscar por documento ou parte..." onSearch={(v) => { setPage(0); setSearch(v); }} />
        <TextField
          select size="small" label="Situação" value={status}
          onChange={(e) => { setPage(0); setStatus(e.target.value as FinancialStatus | ''); }}
          sx={{ minWidth: 180, bgcolor: 'background.paper' }}
        >
          <MenuItem value="">Todas</MenuItem>
          <MenuItem value="em_aberto">Em aberto</MenuItem>
          <MenuItem value="parcial">Parcial</MenuItem>
          <MenuItem value="vencido">Vencido</MenuItem>
          <MenuItem value="quitado">{isReceivable ? 'Recebido' : 'Pago'}</MenuItem>
          <MenuItem value="cancelado">Cancelado</MenuItem>
        </TextField>
      </Stack>
      <Box sx={{ height: 560, mt: 2 }}>
        <DataGrid
          rows={data?.items ?? []}
          columns={columns}
          loading={isFetching}
          rowCount={data?.total ?? 0}
          paginationMode="server"
          paginationModel={{ page, pageSize }}
          onPaginationModelChange={(m) => { setPage(m.page); setPageSize(m.pageSize); }}
          pageSizeOptions={[10, 20, 50]}
          disableColumnMenu
          disableRowSelectionOnClick
          sx={{ bgcolor: 'background.paper' }}
        />
      </Box>

      <AccountFormDialog open={formOpen} direction={direction} onClose={() => setFormOpen(false)} />
      <AccountDetailDialog open={detailId != null} accountId={detailId} onClose={() => setDetailId(null)} />
    </Box>
  );
}
