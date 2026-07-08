import DownloadIcon from '@mui/icons-material/Download';
import {
  Box,
  Button,
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

import { ordersApi } from '@/api/endpoints';
import type { ProfitPeriod } from '@/api/types';
import PageHeader from '@/components/PageHeader';

const money = (n: number) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const isoDate = (d: Date) => d.toISOString().slice(0, 10);

const KPI = ({ label, value, color }: { label: string; value: number; color?: string }) => (
  <Card sx={{ flex: 1, minWidth: 160 }}>
    <CardContent>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography variant="h6" color={color}>{money(value)}</Typography>
    </CardContent>
  </Card>
);

export default function ProfitReportPage() {
  const today = new Date();
  const firstOfYear = new Date(today.getFullYear(), 0, 1);
  const [start, setStart] = useState(isoDate(firstOfYear));
  const [end, setEnd] = useState(isoDate(today));
  const [groupBy, setGroupBy] = useState<'day' | 'month'>('month');

  const { data, isFetching } = useQuery({
    queryKey: ['profit-report', start, end, groupBy],
    queryFn: () => ordersApi.profitReport({ start, end, group_by: groupBy }),
  });

  const downloadCsv = () => {
    if (!data) return;
    const header = ['Periodo', 'Pedidos', 'Receita', 'Custo', 'Custo extra', 'Lucro'];
    const line = (p: ProfitPeriod) =>
      [p.period, p.orders, p.revenue, p.cost, p.extra_cost, p.profit].join(';');
    const csv = [
      header.join(';'),
      ...data.periods.map(line),
      line({ ...data.totals, period: 'TOTAL' }),
    ].join('\n');
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lucro_${start}_${end}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const totals = data?.totals;

  return (
    <Box>
      <PageHeader title="Relatório de Lucro" subtitle="Lucro por período (pedidos confirmados)" />

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3 }} alignItems={{ sm: 'center' }}>
        <TextField
          label="Início" type="date" size="small" value={start}
          onChange={(e) => setStart(e.target.value)} InputLabelProps={{ shrink: true }}
        />
        <TextField
          label="Fim" type="date" size="small" value={end}
          onChange={(e) => setEnd(e.target.value)} InputLabelProps={{ shrink: true }}
        />
        <TextField
          select label="Agrupar por" size="small" value={groupBy}
          onChange={(e) => setGroupBy(e.target.value as 'day' | 'month')} sx={{ minWidth: 150 }}
        >
          <MenuItem value="day">Dia</MenuItem>
          <MenuItem value="month">Mês</MenuItem>
        </TextField>
        <Box sx={{ flex: 1 }} />
        <Button
          variant="outlined" startIcon={<DownloadIcon />} onClick={downloadCsv}
          disabled={!data?.periods.length}
        >
          Baixar CSV
        </Button>
      </Stack>

      {totals && (
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3 }}>
          <KPI label="Receita" value={totals.revenue} />
          <KPI label="Custo dos produtos" value={totals.cost} />
          <KPI label="Custo extra" value={totals.extra_cost} />
          <KPI label="Lucro" value={totals.profit} color={totals.profit >= 0 ? 'success.main' : 'error.main'} />
        </Stack>
      )}

      <Card>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Período</TableCell>
              <TableCell align="right">Pedidos</TableCell>
              <TableCell align="right">Receita</TableCell>
              <TableCell align="right">Custo</TableCell>
              <TableCell align="right">Custo extra</TableCell>
              <TableCell align="right">Lucro</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.periods.map((p) => (
              <TableRow key={p.period}>
                <TableCell>{p.period}</TableCell>
                <TableCell align="right">{p.orders}</TableCell>
                <TableCell align="right">{money(p.revenue)}</TableCell>
                <TableCell align="right">{money(p.cost)}</TableCell>
                <TableCell align="right">{money(p.extra_cost)}</TableCell>
                <TableCell align="right" sx={{ color: p.profit >= 0 ? 'success.main' : 'error.main' }}>
                  {money(p.profit)}
                </TableCell>
              </TableRow>
            ))}
            {!isFetching && !data?.periods.length && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Typography variant="body2" color="text.secondary">
                    Nenhum pedido confirmado no período.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </Box>
  );
}
