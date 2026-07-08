import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';
import { describe, expect, it, vi } from 'vitest';

import PageHeader from './PageHeader';
import { theme } from '@/theme';

function renderWithTheme(ui: ReactElement) {
  return render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>);
}

describe('PageHeader', () => {
  it('renders the title and subtitle', () => {
    renderWithTheme(<PageHeader title="Produtos" subtitle="Lista" />);
    expect(screen.getByText('Produtos')).toBeInTheDocument();
    expect(screen.getByText('Lista')).toBeInTheDocument();
  });

  it('fires the action callback when the button is clicked', () => {
    const onAction = vi.fn();
    renderWithTheme(<PageHeader title="Produtos" actionLabel="Novo" onAction={onAction} />);
    fireEvent.click(screen.getByRole('button', { name: 'Novo' }));
    expect(onAction).toHaveBeenCalledOnce();
  });
});
