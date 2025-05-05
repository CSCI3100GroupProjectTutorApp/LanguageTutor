import { getAuthToken } from './authService';

// License Types
export interface LicenseStatus {
  has_valid_license: boolean;
  license_key?: string;
  activated_at?: string;
  message?: string;
}

// Check the current user's license status
export const getLicenseStatus = async (): Promise<LicenseStatus> => {
  const token = await getAuthToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch('http://localhost:8000/users/license-status', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error('Failed to get license status');
  }

  return await response.json();
};

// Activate a license key for the current user
export const activateLicense = async (licenseKey: string): Promise<{ message: string }> => {
  const token = await getAuthToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch('http://localhost:8000/users/activate-license', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ license_key: licenseKey })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to activate license');
  }

  return await response.json();
};

// Request a new license key (may be sent via email or returned directly)
export const requestLicense = async (): Promise<{ success: boolean, license_key?: string, message: string }> => {
  const token = await getAuthToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch('http://localhost:8000/users/request-license', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error('Failed to request license');
  }

  return await response.json();
}; 