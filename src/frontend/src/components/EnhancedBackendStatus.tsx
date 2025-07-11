import React from 'react';
import { Chip, Grid, Paper, Typography } from '@mui/material';
import { useServiceStatus } from '../hooks/useServiceStatus';

const EnhancedBackendStatus: React.FC = () => {
  const { serviceStatuses } = useServiceStatus();

  const getStatusColor = (status: 'online' | 'offline' | 'checking') => {
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'error';
      case 'checking':
        return 'warning';
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        System Status
      </Typography>
      <Grid container spacing={1}>
        {serviceStatuses.map((service) => (
          <Grid item key={service.id}>
            <Chip
              icon={service.icon}
              label={`${service.displayName} - ${service.status}`}
              color={getStatusColor(service.status)}
              size="small"
              sx={{ fontSize: '0.75rem' }}
            />
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
};

export default EnhancedBackendStatus;
