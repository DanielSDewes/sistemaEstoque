import { createTheme, type PaletteMode, type Theme } from '@mui/material/styles';

/** Build the application theme for the given color mode (light/dark). */
export function createAppTheme(mode: PaletteMode): Theme {
  const isDark = mode === 'dark';
  return createTheme({
    palette: {
      mode,
      primary: isDark
        ? { main: '#5b9bd5', light: '#7fb2e0', dark: '#3a6ea5' }
        : { main: '#1F4E78', light: '#2f6ba8', dark: '#143654' },
      secondary: { main: '#0f9d58' },
      background: isDark
        ? { default: '#0e1116', paper: '#171d26' }
        : { default: '#f4f6fa', paper: '#ffffff' },
      error: { main: isDark ? '#f2645a' : '#d32f2f' },
      warning: { main: '#ed6c02' },
      success: { main: '#2e7d32' },
    },
    shape: { borderRadius: 10 },
    typography: {
      fontFamily: 'Roboto, "Segoe UI", Arial, sans-serif',
      h4: { fontWeight: 700 },
      h5: { fontWeight: 700 },
      h6: { fontWeight: 600 },
    },
    components: {
      MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
      MuiButton: { defaultProps: { disableElevation: true } },
      MuiCard: { styleOverrides: { root: { borderRadius: 12 } } },
    },
  });
}

/** Default (light) theme, kept for non-context consumers such as tests. */
export const theme = createAppTheme('light');
