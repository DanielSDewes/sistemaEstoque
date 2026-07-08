import { Box, Button, Stack, Typography } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actionLabel?: string;
  onAction?: () => void;
  children?: ReactNode;
}

export default function PageHeader({
  title,
  subtitle,
  actionLabel,
  onAction,
  children,
}: PageHeaderProps) {
  return (
    <Stack
      direction={{ xs: 'column', sm: 'row' }}
      justifyContent="space-between"
      alignItems={{ xs: 'flex-start', sm: 'center' }}
      spacing={2}
      sx={{ mb: 3 }}
    >
      <Box>
        <Typography variant="h5">{title}</Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Box>
      <Stack direction="row" spacing={1}>
        {children}
        {actionLabel && onAction && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </Stack>
    </Stack>
  );
}
