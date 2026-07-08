import EditIcon from '@mui/icons-material/Edit';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import SwapVertIcon from '@mui/icons-material/SwapVert';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { Avatar, Box, Button, Chip, IconButton, MenuItem, Stack, TextField, Tooltip } from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { assetUrl } from '@/api/client';
import { brandsApi, categoriesApi, groupsApi, productsApi, suppliersApi } from '@/api/endpoints';
import type { Product } from '@/api/types';
import PageHeader from '@/components/PageHeader';
import SearchBar from '@/components/SearchBar';
import { useAuth } from '@/auth/AuthContext';
import ImportDialog from '@/pages/products/ImportDialog';
import MovementDialog from '@/pages/products/MovementDialog';
import ProductDetailDialog from '@/pages/products/ProductDetailDialog';
import ProductFormDialog from '@/pages/products/ProductFormDialog';

export default function ProductsPage() {
  const { hasPermission } = useAuth();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<{
    category_id?: number;
    group_id?: number;
    brand_id?: number;
    supplier_id?: number;
    is_active?: boolean;
  }>({});
  const [formOpen, setFormOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [movementFor, setMovementFor] = useState<Product | null>(null);
  const [detailFor, setDetailFor] = useState<Product | null>(null);
  const [editing, setEditing] = useState<Product | null>(null);

  const canCreate = hasPermission('product:create');
  const canEdit = hasPermission('product:update');
  const canMove = hasPermission('movement:create');

  const { data: categories } = useQuery({ queryKey: ['categories', 'all'], queryFn: () => categoriesApi.list({ size: 200 }) });
  const { data: groups } = useQuery({ queryKey: ['groups', 'all'], queryFn: () => groupsApi.list({ size: 200 }) });
  const { data: brands } = useQuery({ queryKey: ['brands', 'all'], queryFn: () => brandsApi.list({ size: 200 }) });
  const { data: suppliers } = useQuery({ queryKey: ['suppliers', 'all'], queryFn: () => suppliersApi.list({ size: 200 }) });

  const { data, isFetching } = useQuery({
    queryKey: ['products', page, pageSize, search, filters],
    queryFn: () => productsApi.list({ page: page + 1, size: pageSize, q: search, ...filters }),
  });

  const setFilter = (key: string, value: number | boolean | undefined) => {
    setPage(0);
    setFilters((f) => {
      const next = { ...f };
      if (value === undefined) delete (next as Record<string, unknown>)[key];
      else (next as Record<string, unknown>)[key] = value;
      return next;
    });
  };

  const columns: GridColDef<Product>[] = [
    {
      field: 'photo_url',
      headerName: '',
      width: 56,
      sortable: false,
      renderCell: (p) => (
        <Avatar src={assetUrl(p.value)} variant="rounded" sx={{ width: 32, height: 32 }}>
          {p.row.name[0]}
        </Avatar>
      ),
    },
    { field: 'internal_code', headerName: 'Código', width: 110 },
    { field: 'name', headerName: 'Produto', flex: 1, minWidth: 180 },
    { field: 'unit', headerName: 'Un.', width: 64 },
    { field: 'category', headerName: 'Categoria', width: 130, valueGetter: (_v, row) => row.category?.name ?? '—' },
    {
      field: 'current',
      headerName: 'Saldo',
      width: 100,
      valueGetter: (_v, row) => row.stock?.current ?? 0,
      renderCell: (p) => (
        <Chip
          size="small"
          label={p.row.stock?.current ?? 0}
          color={p.row.stock?.below_minimum ? 'warning' : 'default'}
          variant={p.row.stock?.below_minimum ? 'filled' : 'outlined'}
        />
      ),
    },
    {
      field: 'average_cost',
      headerName: 'Custo médio',
      width: 120,
      valueGetter: (v) => (v ? `R$ ${Number(v).toFixed(2)}` : '—'),
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 100,
      renderCell: (p) => (
        <Chip size="small" label={p.value ? 'Ativo' : 'Inativo'} color={p.value ? 'success' : 'default'} />
      ),
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 140,
      sortable: false,
      renderCell: (p) => (
        <Stack direction="row">
          <Tooltip title="Detalhes">
            <IconButton size="small" onClick={() => setDetailFor(p.row)}>
              <InfoOutlinedIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {canMove && p.row.is_active && (
            <Tooltip title="Movimentar">
              <IconButton size="small" onClick={() => setMovementFor(p.row)}>
                <SwapVertIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {canEdit && (
            <Tooltip title="Editar">
              <IconButton size="small" onClick={() => { setEditing(p.row); setFormOpen(true); }}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Stack>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Produtos"
        subtitle="Busca inteligente e filtros avançados"
        actionLabel={canCreate ? 'Novo produto' : undefined}
        onAction={canCreate ? () => { setEditing(null); setFormOpen(true); } : undefined}
      >
        {canCreate && (
          <Button variant="outlined" startIcon={<UploadFileIcon />} onClick={() => setImportOpen(true)}>
            Importar CSV
          </Button>
        )}
      </PageHeader>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 2 }} flexWrap="wrap" useFlexGap>
        <SearchBar
          placeholder="Buscar: código, barras, SKU, nome..."
          onSearch={(v) => { setPage(0); setSearch(v); }}
        />
        <TextField select size="small" label="Categoria" sx={{ minWidth: 150 }} defaultValue=""
          onChange={(e) => setFilter('category_id', e.target.value ? Number(e.target.value) : undefined)}>
          <MenuItem value="">Todas</MenuItem>
          {categories?.items.map((c) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Grupo" sx={{ minWidth: 150 }} defaultValue=""
          onChange={(e) => setFilter('group_id', e.target.value ? Number(e.target.value) : undefined)}>
          <MenuItem value="">Todos</MenuItem>
          {groups?.items.map((g) => <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Marca" sx={{ minWidth: 140 }} defaultValue=""
          onChange={(e) => setFilter('brand_id', e.target.value ? Number(e.target.value) : undefined)}>
          <MenuItem value="">Todas</MenuItem>
          {brands?.items.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Fornecedor" sx={{ minWidth: 160 }} defaultValue=""
          onChange={(e) => setFilter('supplier_id', e.target.value ? Number(e.target.value) : undefined)}>
          <MenuItem value="">Todos</MenuItem>
          {suppliers?.items.map((s) => <MenuItem key={s.id} value={s.id}>{s.trade_name || s.legal_name}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Status" sx={{ minWidth: 120 }} defaultValue=""
          onChange={(e) => setFilter('is_active', e.target.value === '' ? undefined : e.target.value === 'true')}>
          <MenuItem value="">Todos</MenuItem>
          <MenuItem value="true">Ativos</MenuItem>
          <MenuItem value="false">Inativos</MenuItem>
        </TextField>
      </Stack>

      <Box sx={{ height: 560 }}>
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

      <ProductFormDialog open={formOpen} product={editing} onClose={() => setFormOpen(false)} />
      <MovementDialog open={!!movementFor} product={movementFor} onClose={() => setMovementFor(null)} />
      <ProductDetailDialog open={!!detailFor} product={detailFor} onClose={() => setDetailFor(null)} />
      <ImportDialog open={importOpen} onClose={() => setImportOpen(false)} />
    </Box>
  );
}
