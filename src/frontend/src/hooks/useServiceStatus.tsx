// src/frontend/src/hooks/useServiceStatus.tsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import { serviceConfigs, iconMapping, type ServiceConfig } from '../config/services';
import { apiUrlBuilder } from '../config/api';
import Logger from '../utils/logger';

export interface ServiceStatus {
  id: string;
  name: string;
  displayName: string;
  status: 'online' | 'offline' | 'checking';
  icon: React.ReactElement;
}

export const useServiceStatus = () => {
  const [serviceStatuses, setServiceStatuses] = useState<ServiceStatus[]>([]);

  // Helper function to convert icon string to React element
  const getIconElement = (iconName: string): React.ReactElement => {
    const IconComponent = iconMapping[iconName as keyof typeof iconMapping];
    if (IconComponent) {
      return <IconComponent />;
    }
    return <div />;
  };

  useEffect(() => {
    const initialStatuses: ServiceStatus[] = serviceConfigs
      .filter(s => s.enabled)
      .map(config => ({
        id: config.id,
        name: config.name,
        displayName: config.displayName,
        status: 'checking' as const,
        icon: getIconElement(config.icon), // Convert string to React element
      }));
    setServiceStatuses(initialStatuses);

    const checkStatus = async (service: ServiceConfig): Promise<'online' | 'offline'> => {
      try {
        // Build the full backend URL for the health check
        const healthUrl = apiUrlBuilder.buildUrl(service.healthCheckUrl);
        const response = await axios.get(healthUrl);
        if (response.status === 200 && response.data.status === 'ok') {
          return 'online';
        }
        return 'offline';
      } catch (error) {
        Logger.error(`Health check failed for ${service.name}`, 'useServiceStatus.tsx', 'checkStatus', 32, error);
        return 'offline';
      }
    };

    const updateAllStatuses = async () => {
      const promises = serviceConfigs
        .filter(s => s.enabled)
        .map(async config => {
          const status = await checkStatus(config);
          return {
            id: config.id,
            name: config.name,
            displayName: config.displayName,
            status,
            icon: getIconElement(config.icon), // Convert string to React element
          };
        });
      const newStatuses = await Promise.all(promises);
      setServiceStatuses(newStatuses);
    };

    updateAllStatuses();
    const interval = setInterval(updateAllStatuses, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return { serviceStatuses };
};
