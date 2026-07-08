import SearchIcon from '@mui/icons-material/Search';
import { InputAdornment, TextField } from '@mui/material';
import { useEffect, useState } from 'react';

interface SearchBarProps {
  placeholder?: string;
  onSearch: (value: string) => void;
  debounceMs?: number;
}

/** Debounced search input. */
export default function SearchBar({ placeholder = 'Buscar...', onSearch, debounceMs = 400 }: SearchBarProps) {
  const [value, setValue] = useState('');

  useEffect(() => {
    const t = setTimeout(() => onSearch(value.trim()), debounceMs);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <TextField
      size="small"
      fullWidth
      placeholder={placeholder}
      value={value}
      onChange={(e) => setValue(e.target.value)}
      sx={{ maxWidth: 420, bgcolor: 'background.paper' }}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon fontSize="small" />
          </InputAdornment>
        ),
      }}
    />
  );
}
