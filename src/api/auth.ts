/**
 * Authentication service for the language tutoring application
 */
import { apiClient, setAuthToken, clearAuthToken, APIError } from './client';
import { API_ENDPOINTS } from './config';

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

/**
 * Login user with username and password
 */
export const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  try {
    // Convert credentials to FormData
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await apiClient.post<AuthResponse>(
      API_ENDPOINTS.LOGIN, 
      formData.toString(),
      { 'Content-Type': 'application/x-www-form-urlencoded' }
    );
    
    // Store the token
    if (response.access_token) {
      setAuthToken(response.access_token);
      // Store tokens in localStorage for web
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.setItem('auth_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
      }
    }
    return response;
  } catch (error) {
    console.error('Login failed:', error);
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
    console.error('Registration failed:', error);
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
    console.error('Logout failed:', error);
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
    console.error('Token refresh failed:', error);
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