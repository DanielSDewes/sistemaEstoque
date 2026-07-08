import DescriptionIcon from '@mui/icons-material/Description';
import GridOnIcon from '@mui/icons-material/GridOn';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { Box, Button, Card, CardContent, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';

import { apiErrorMessage } from '@/api/client';
import { reportsApi } from '@/api/endpoints';
import PageHeader from '@/components/PageHeader';

const FORMATS = [
  { fmt: 'xlsx', label: 'Excel', icon: GridOnIcon, color: '#0f9d58' },
  { fmt: 'pdf', label: 'PDF', icon: PictureAsPdfIcon, color: '#c0392b' },
  { fmt: 'csv', label: 'CSV', icon: DescriptionIcon, color: '#2f6ba8' },
];

export default function ReportsPage() {
  const { enqueueSnackbar } = useSnackbar();
  const { data: reports } = useQuery({ queryKey: ['reports'], queryFn: () => reportsApi.list() });

  const download = async (report: string, fmt: string) => {
    try {
      const blob = await reportsApi.download(report, fmt);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report}.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      enqueueSnackbar(apiErrorMessage(e, 'Falha ao exportar'), { variant: 'error' });
    }
  };

  return (
    <Box>
      <PageHeader title="Relatórios" subtitle="Exportação para Excel, PDF e CSV" />
      <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' } }}>
        {Object.entries(reports ?? {}).map(([key, title]) => (
          <Card key={key}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                {title}
              </Typography>
              <Stack direction="row" spacing={1}>
                {FORMATS.map((f) => {
                  const Icon = f.icon;
                  return (
                    <Button
                      key={f.fmt}
                      size="small"
                      variant="outlined"
                      startIcon={<Icon sx={{ color: f.color }} />}
                      onClick={() => download(key, f.fmt)}
                    >
                      {f.label}
                    </Button>
                  );
                })}
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
}
