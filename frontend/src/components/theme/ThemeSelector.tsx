import { FormControl, InputLabel, MenuItem, Select } from '@mui/material';

export type ThemeMode = 'light' | 'dark' | 'system';

interface Props {
  mode: ThemeMode;
  onChange: (mode: ThemeMode) => void;
}

export const ThemeSelector = ({ mode, onChange }: Props) => (
  <FormControl fullWidth size="small" sx={{ minWidth: 120 }}>
    <InputLabel id="theme-select-label">Theme</InputLabel>
    <Select
      labelId="theme-select-label"
      label="Theme"
      value={mode}
      onChange={(e) => onChange(e.target.value as ThemeMode)}
    >
      <MenuItem value="light">Light</MenuItem>
      <MenuItem value="dark">Dark</MenuItem>
      <MenuItem value="system">System</MenuItem>
    </Select>
  </FormControl>
);
