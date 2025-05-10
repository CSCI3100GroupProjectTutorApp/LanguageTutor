/**
 * Authentication service for the language tutoring application
 */
import { apiClient, setAuthToken, clearAuthToken, APIError } from './client';
import { API_ENDPOINTS } from './config';
import { API_BASE_URL } from '../../assets/constants/API_URL';
import { setAuthToken as setAuthTokenService, setRefreshToken} from '../services/authService';

// Types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  username: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
    username: string;
    name: string;
  };
}
interface LoginResponse {
  access_token: string;
  token_type: string;
  refresh_token: string;
}


/**
 * Login user with username and password
 */
export const login = async ({ username, password }: { username: string; password: string }) => {
  try {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username,
        password,
      }).toString(),
    });

    if (!response.ok) {
      throw new Error(response.status.toString());
    }

    const data: LoginResponse = await response.json();
    // Store the token in authService
    setAuthTokenService(data.access_token);
    //setRefreshToken(data.refresh_token)
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Register a new user
 */
export const register = async (userData: RegisterData): Promise<{ message: string }> => {
  try {
    const response = await apiClient.post<any>(API_ENDPOINTS.REGISTER, userData);
    
    // Check if the response contains any indication of user already existing
    if (response.detail?.includes('already exists') || 
        response.message?.includes('already exists') ||
        response.error?.includes('already exists')) {
      throw new APIError(
        'Username or email already exists. Please choose different ones.',
        409,
        response
      );
    }
    
    return { message: "Registration successful! Please log in." };
  } catch (error) {
    throw error;
  }
};

/**
 * Logout user
 */
export const logout = async (): Promise<void> => {
  try {
    await apiClient.post(API_ENDPOINTS.LOGOUT, {});
    clearAuthToken();
    // Remove tokens from localStorage for web
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
    }
  } catch (error) {
    throw error;
  }
};

/**
 * Refresh the access token using the refresh token
 */
export const refreshToken = async (): Promise<{ access_token: string }> => {
  try {
    // Get refresh token from localStorage for web
    let refreshTokenValue = '';
    if (typeof window !== 'undefined' && window.localStorage) {
      refreshTokenValue = localStorage.getItem('refresh_token') || '';
    }
    
    if (!refreshTokenValue) {
      throw new Error('No refresh token available');
    }
    
    const response = await apiClient.post<{ access_token: string }>(
      API_ENDPOINTS.REFRESH_TOKEN, 
      { refresh_token: refreshTokenValue }
    );
    
    // Update the token
    if (response.access_token) {
      setAuthToken(response.access_token);
      // Update token in localStorage for web
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.setItem('auth_token', response.access_token);
      }
    }
    
    return response;
  } catch (error) {
    throw error;
  }
};

/**
 * Initialize auth from stored token
 */
export const initializeAuth = (): boolean => {
  // Check for stored token in localStorage for web
  if (typeof window !== 'undefined' && window.localStorage) {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      setAuthToken(storedToken);
      return true;
    }
  }
  return false;
}; 