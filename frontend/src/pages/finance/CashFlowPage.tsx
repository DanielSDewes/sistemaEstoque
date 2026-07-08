import {
  Box,
  Card,
  CardContent,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { financeApi } from '@/api/endpoints';
import PageHeader from '@/components/PageHeader';
import { money } from '@/pages/finance/financeUtils';

const isoDate = (d: Date) => d.toISOString().slice(0, 10);

const Kpi = ({ label, value, color }: { label: string; value: number; color?: string }) => (
  <Card sx={{ flex: 1, minWidth: 160 }}>
    <CardContent>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography variant="h6" color={color}>{money(value)}</Typography>
    </CardContent>
  </Card>
);

export default function CashFlowPage() {
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
  const end = new Date(today.getFullYear(), today.getMonth() + 2, 0);
  const [from, setFrom] = useState(isoDate(start));
  const [to, setTo] = useState(isoDate(end));
  const [groupBy, setGroupBy] = useState<'day' | 'week' | 'month'>('month');

  const { data } = useQuery({
    queryKey: ['cashflow', from, to, groupBy],
    queryFn: () => financeApi.cashflow({ start: from, end: to, group_by: groupBy }),
  });

  const totals = data?.totals;
  const chartData = (data?.periods ?? []).map((p) => ({
    period: p.period,
    Previsto: p.net_expected,
    Realizado: p.net_realized,
  }));

  return (
    <Box>
      <PageHeader title="Fluxo de Caixa" subtitle="Previsto (contas em aberto) x realizado (baixas)" />

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3 }} alignItems={{ sm: 'center' }}>
        <TextField label="Início" type="date" size="small" value={from} onChange={(e) => setFrom(e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField label="Fim" type="date" size="small" value={to} onChange={(e) => setTo(e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField select label="Agrupar por" size="small" value={groupBy} onChange={(e) => setGroupBy(e.target.value as 'day' | 'week' | 'month')} sx={{ minWidth: 150 }}>
          <MenuItem value="day">Dia</MenuItem>
          <MenuItem value="week">Semana</MenuItem>
          <MenuItem value="month">Mês</MenuItem>
        </TextField>
      </Stack>

      {totals && (
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3 }}>
          <Kpi label="Entradas realizadas" value={totals.inflow_realized} color="success.main" />
          <Kpi label="Saídas realizadas" value={totals.outflow_realized} color="error.main" />
          <Kpi label="Saldo realizado" value={totals.net_realized} color={totals.net_realized >= 0 ? 'success.main' : 'error.main'} />
          <Kpi label="Saldo previsto" value={totals.net_expected} />
        </Stack>
      )}

      {chartData.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip formatter={(v: number) => money(v)} />
                <Legend />
                <Bar dataKey="Previsto" fill="#2f6ba8" />
                <Bar dataKey="Realizado" fill="#0f9d58" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      <Card>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Período</TableCell>
              <TableCell align="right">Entradas prev.</TableCell>
              <TableCell align="right">Saídas prev.</TableCell>
              <TableCell align="right">Entradas real.</TableCell>
              <TableCell align="right">Saídas real.</TableCell>
              <TableCell align="right">Saldo real.</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.periods.map((p) => (
              <TableRow key={p.period}>
                <TableCell>{p.period}</TableCell>
                <TableCell align="right">{money(p.inflow_expected)}</TableCell>
                <TableCell align="right">{money(p.outflow_expected)}</TableCell>
                <TableCell align="right">{money(p.inflow_realized)}</TableCell>
                <TableCell align="right">{money(p.outflow_realized)}</TableCell>
                <TableCell align="right" sx={{ color: p.net_realized >= 0 ? 'success.main' : 'error.main' }}>
                  {money(p.net_realized)}
                </TableCell>
              </TableRow>
            ))}
            {!data?.periods.length && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Typography variant="body2" color="text.secondary">Sem lançamentos no período.</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </Box>
  );
}
