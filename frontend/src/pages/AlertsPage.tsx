import EventBusyIcon from '@mui/icons-material/EventBusy';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';

import { alertsApi } from '@/api/endpoints';
import PageHeader from '@/components/PageHeader';

function Kpi({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h4" fontWeight={800} color={color}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function AlertsPage() {
  const { data: summary } = useQuery({ queryKey: ['alerts', 'summary'], queryFn: () => alertsApi.summary() });
  const { data: belowMin } = useQuery({ queryKey: ['alerts', 'below'], queryFn: () => alertsApi.belowMinimum() });
  const { data: nearExpiry } = useQuery({ queryKey: ['alerts', 'expiry'], queryFn: () => alertsApi.nearExpiry() });

  return (
    <Box>
      <PageHeader title="Central de Alertas" subtitle="Ações recomendadas de reposição e validade" />

      <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr 1fr', md: 'repeat(4, 1fr)' }, mb: 3 }}>
        <Kpi label="Abaixo do mínimo" value={summary?.below_minimum_count ?? 0} color="warning.main" />
        <Kpi label="Sem estoque" value={summary?.out_of_stock_count ?? 0} color="error.main" />
        <Kpi label="Próx. do vencimento" value={summary?.near_expiry_count ?? 0} color="warning.main" />
        <Kpi label="Vencidos" value={summary?.expired_count ?? 0} color="error.main" />
      </Box>

      <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' } }}>
        <Paper sx={{ p: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
            <WarningAmberIcon color="warning" />
            <Typography variant="subtitle1" fontWeight={700}>
              Produtos abaixo do estoque mínimo
            </Typography>
          </Stack>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Código</TableCell>
                <TableCell>Produto</TableCell>
                <TableCell align="right">Saldo</TableCell>
                <TableCell align="right">Mínimo</TableCell>
                <TableCell align="right">Déficit</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {belowMin?.map((i) => (
                <TableRow key={i.product_id}>
                  <TableCell>{i.internal_code}</TableCell>
                  <TableCell>{i.name}</TableCell>
                  <TableCell align="right">{i.current}</TableCell>
                  <TableCell align="right">{i.min_stock}</TableCell>
                  <TableCell align="right">
                    <Chip size="small" color="warning" label={i.deficit} />
                  </TableCell>
                </TableRow>
              ))}
              {!belowMin?.length && (
                <TableRow>
                  <TableCell colSpan={5}>
                    <Stack direction="row" spacing={1} alignItems="center" color="text.secondary">
                      <ReportProblemIcon fontSize="small" />
                      <Typography variant="body2">Nenhum produto abaixo do mínimo.</Typography>
                    </Stack>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Paper>

        <Paper sx={{ p: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
            <EventBusyIcon color="error" />
            <Typography variant="subtitle1" fontWeight={700}>
              Próximos do vencimento
            </Typography>
          </Stack>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Produto</TableCell>
                <TableCell>Lote</TableCell>
                <TableCell>Validade</TableCell>
                <TableCell align="right">Dias</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {nearExpiry?.map((i, idx) => (
                <TableRow key={idx}>
                  <TableCell>{i.name}</TableCell>
                  <TableCell>{i.lot_number}</TableCell>
                  <TableCell>{i.expiry_date}</TableCell>
                  <TableCell align="right">
                    <Chip
                      size="small"
                      color={i.days_remaining <= 7 ? 'error' : 'warning'}
                      label={`${i.days_remaining}d`}
                    />
                  </TableCell>
                </TableRow>
              ))}
              {!nearExpiry?.length && (
                <TableRow>
                  <TableCell colSpan={4}>
                    <Typography variant="body2" color="text.secondary">
                      Nenhum lote próximo do vencimento.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Paper>
      </Box>
    </Box>
  );
}
