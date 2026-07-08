import CategoryIcon from '@mui/icons-material/Category';
import Inventory2Icon from '@mui/icons-material/Inventory2';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import PaidIcon from '@mui/icons-material/Paid';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import SwapVertIcon from '@mui/icons-material/SwapVert';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { Alert, Box, Card, CardContent, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import type { SvgIconComponent } from '@mui/icons-material';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { dashboardApi } from '@/api/endpoints';
import type { NamedSeries } from '@/api/types';

const PIE_COLORS = ['#1F4E78', '#2f6ba8', '#0f9d58', '#ed6c02', '#8e44ad', '#c0392b'];

const currency = (n: number) =>
  n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

function KpiCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: SvgIconComponent;
  color: string;
}) {
  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: `${color}22`,
              color,
            }}
          >
            <Icon />
          </Box>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="h6" noWrap>
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap>
              {label}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Paper sx={{ p: 2, height: 320, display: 'flex', flexDirection: 'column' }}>
      <Typography variant="subtitle1" fontWeight={700} gutterBottom>
        {title}
      </Typography>
      <Box sx={{ flex: 1 }}>
        <ResponsiveContainer width="100%" height="100%">
          {children as React.ReactElement}
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
}

function mergeEntriesExits(series: NamedSeries[]) {
  const labels = new Set<string>();
  series.forEach((s) => s.points.forEach((p) => labels.add(p.label)));
  return Array.from(labels)
    .sort()
    .map((label) => {
      const row: Record<string, string | number> = { label };
      series.forEach((s) => {
        row[s.name] = s.points.find((p) => p.label === label)?.value ?? 0;
      });
      return row;
    });
}

export default function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.get(14),
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !data) {
    return <Alert severity="error">Não foi possível carregar o dashboard.</Alert>;
  }

  const { kpis } = data;
  const entriesExits = mergeEntriesExits(data.entries_vs_exits);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Dashboard
      </Typography>

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          mb: 3,
          gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(3, 1fr)', lg: 'repeat(6, 1fr)' },
        }}
      >
        <KpiCard label="Produtos" value={kpis.total_products} icon={Inventory2Icon} color="#1F4E78" />
        <KpiCard label="Sem estoque" value={kpis.products_no_stock} icon={ReportProblemIcon} color="#c0392b" />
        <KpiCard label="Abaixo do mínimo" value={kpis.products_below_min} icon={WarningAmberIcon} color="#ed6c02" />
        <KpiCard label="Movim. hoje" value={kpis.movements_today} icon={SwapVertIcon} color="#2f6ba8" />
        <KpiCard label="Fornecedores" value={kpis.total_suppliers} icon={LocalShippingIcon} color="#0f9d58" />
        <KpiCard label="Valor em estoque" value={currency(kpis.total_stock_value)} icon={PaidIcon} color="#8e44ad" />
      </Box>

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' },
        }}
      >
        <ChartCard title="Entradas x Saídas (14 dias)">
          <LineChart data={entriesExits}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" fontSize={11} />
            <YAxis fontSize={11} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="Entradas" stroke="#0f9d58" strokeWidth={2} />
            <Line type="monotone" dataKey="Saidas" stroke="#c0392b" strokeWidth={2} />
          </LineChart>
        </ChartCard>

        <ChartCard title="Estoque por categoria">
          <PieChart>
            <Tooltip />
            <Pie
              data={data.stock_by_category}
              dataKey="value"
              nameKey="label"
              cx="50%"
              cy="50%"
              outerRadius={90}
              label={(e) => e.label}
            >
              {data.stock_by_category.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        </ChartCard>

        <ChartCard title="Movimentações por dia">
          <AreaChart data={data.movements_by_day}>
            <defs>
              <linearGradient id="mov" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1F4E78" stopOpacity={0.7} />
                <stop offset="95%" stopColor="#1F4E78" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" fontSize={11} />
            <YAxis fontSize={11} />
            <Tooltip />
            <Area type="monotone" dataKey="value" stroke="#1F4E78" fill="url(#mov)" name="Movimentações" />
          </AreaChart>
        </ChartCard>

        <ChartCard title="Top produtos movimentados">
          <BarChart data={data.top_moved_products} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" fontSize={11} />
            <YAxis type="category" dataKey="label" width={120} fontSize={10} />
            <Tooltip />
            <Bar dataKey="value" fill="#2f6ba8" name="Quantidade" radius={[0, 4, 4, 0]}>
              {data.top_moved_products.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ChartCard>
      </Box>

      <Stack direction="row" spacing={1} sx={{ mt: 2 }} alignItems="center">
        <CategoryIcon fontSize="small" color="action" />
        <Typography variant="body2" color="text.secondary">
          Quantidade total armazenada: <strong>{kpis.total_stock_quantity.toLocaleString('pt-BR')}</strong>
          {' · '}Próximos ao vencimento: <strong>{kpis.products_near_expiry}</strong>
        </Typography>
      </Stack>
    </Box>
  );
}
