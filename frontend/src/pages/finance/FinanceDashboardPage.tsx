import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import SavingsIcon from '@mui/icons-material/Savings';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import {
  Box,
  Card,
  CardContent,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import type { SvgIconComponent } from '@mui/icons-material';

import { financeApi } from '@/api/endpoints';
import PageHeader from '@/components/PageHeader';
import { money } from '@/pages/finance/financeUtils';

function Kpi({ label, value, icon: Icon, color }: { label: string; value: number; icon: SvgIconComponent; color: string }) {
  return (
    <Card sx={{ flex: 1, minWidth: 200 }}>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Box sx={{ width: 44, height: 44, borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: `${color}22`, color }}>
            <Icon />
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">{label}</Typography>
            <Typography variant="h6">{money(value)}</Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function FinanceDashboardPage() {
  const { data } = useQuery({ queryKey: ['finance-dashboard'], queryFn: () => financeApi.dashboard() });

  return (
    <Box>
      <PageHeader title="Painel Financeiro" subtitle="Visão geral de recebimentos, pagamentos e caixa" />

      {data && (
        <Stack spacing={3}>
          <Box>
            <Typography variant="overline" color="text.secondary">A Receber</Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mt: 1 }}>
              <Kpi label="Em aberto" value={data.receivable_open} icon={TrendingUpIcon} color="#0f9d58" />
              <Kpi label="Vencido" value={data.receivable_overdue} icon={TrendingUpIcon} color="#c0392b" />
              <Kpi label="Recebido hoje" value={data.received_today} icon={TrendingUpIcon} color="#2f6ba8" />
              <Kpi label="Recebido no mês" value={data.received_month} icon={TrendingUpIcon} color="#1F4E78" />
            </Stack>
          </Box>

          <Box>
            <Typography variant="overline" color="text.secondary">A Pagar</Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mt: 1 }}>
              <Kpi label="Em aberto" value={data.payable_open} icon={TrendingDownIcon} color="#ed6c02" />
              <Kpi label="Vencido" value={data.payable_overdue} icon={TrendingDownIcon} color="#c0392b" />
              <Kpi label="Pago hoje" value={data.paid_today} icon={TrendingDownIcon} color="#2f6ba8" />
              <Kpi label="Pago no mês" value={data.paid_month} icon={TrendingDownIcon} color="#1F4E78" />
            </Stack>
          </Box>

          <Box>
            <Typography variant="overline" color="text.secondary">Caixa</Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mt: 1 }}>
              <Kpi label="Saldo total em caixa" value={data.cash_total} icon={AccountBalanceIcon} color="#8e44ad" />
              <Card sx={{ flex: 2, minWidth: 260 }}>
                <CardContent>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                    <SavingsIcon fontSize="small" color="action" />
                    <Typography variant="subtitle2">Saldo por conta</Typography>
                  </Stack>
                  <Table size="small">
                    <TableHead>
                      <TableRow><TableCell>Conta</TableCell><TableCell align="right">Saldo</TableCell></TableRow>
                    </TableHead>
                    <TableBody>
                      {data.banks.map((b) => (
                        <TableRow key={b.id}>
                          <TableCell>{b.name}</TableCell>
                          <TableCell align="right">{money(b.balance)}</TableCell>
                        </TableRow>
                      ))}
                      {!data.banks.length && (
                        <TableRow><TableCell colSpan={2}><Typography variant="body2" color="text.secondary">Nenhuma conta bancária.</Typography></TableCell></TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </Stack>
          </Box>
        </Stack>
      )}
    </Box>
  );
}
