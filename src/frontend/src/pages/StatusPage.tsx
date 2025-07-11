import React from 'react';
import { Container, Typography } from '@mui/material';
import EnhancedBackendStatus from '../components/EnhancedBackendStatus';

const StatusPage: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Service Status
      </Typography>
      <EnhancedBackendStatus />
    </Container>
  );
};

export default StatusPage;
