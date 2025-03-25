/**
 * API client for the language tutoring application
 * Handles API requests to the backend
 */
import { API_BASE_URL, DEFAULT_HEADERS, REQUEST_TIMEOUT } from './config';

// Token management
let accessToken: string | null = null;

/**
 * Sets the authentication token for API requests
 */
export const setAuthToken = (token: string) => {
  accessToken = token;
};

/**
 * Clears the authentication token
 */
export const clearAuthToken = () => {
  accessToken = null;
};

/**
 * Get authentication headers with token if available
 */
const getAuthHeaders = () => {
  if (accessToken) {
    return {
      ...DEFAULT_HEADERS,
      'Authorization': `Bearer ${accessToken}`
    };
  }
  return DEFAULT_HEADERS;
};

/**
 * Generic API request function
 */
const apiRequest = async <T>(
  endpoint: string, 
  method: string = 'GET', 
  data: any = null,
  customHeaders: Record<string, string> = {}
): Promise<T> => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = {
    ...getAuthHeaders(),
    ...customHeaders
  };
  
  const options: RequestInit = {
    method,
    headers,
    credentials: 'include',
  };
  
  if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    options.body = JSON.stringify(data);
  }
  
  // Create a timeout promise
  const timeoutPromise = new Promise<never>((_, reject: (reason?: any) => void) => {
    setTimeout(() => reject(new Error('Request timeout')), REQUEST_TIMEOUT);
  });
  
  // Race between fetch and timeout
  try {
    const response = await Promise.race<Response>([
      fetch(url, options),
      timeoutPromise
    ]);
    
    if (!response.ok) {
      // Try to parse error response
      const errorData = await response.json().catch(() => null);
      throw new Error(
        errorData?.detail || `API error: ${response.status} ${response.statusText}`
      );
    }
    
    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.indexOf('application/json') !== -1) {
      return await response.json() as T;
    }
    
    return await response.text() as unknown as T;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

/**
 * API client with convenience methods for different HTTP methods
 */
export const apiClient = {
  get: <T>(endpoint: string, customHeaders = {}) => 
    apiRequest<T>(endpoint, 'GET', null, customHeaders),
    
  post: <T>(endpoint: string, data: any, customHeaders = {}) => 
    apiRequest<T>(endpoint, 'POST', data, customHeaders),
    
  put: <T>(endpoint: string, data: any, customHeaders = {}) => 
    apiRequest<T>(endpoint, 'PUT', data, customHeaders),
    
  patch: <T>(endpoint: string, data: any, customHeaders = {}) => 
    apiRequest<T>(endpoint, 'PATCH', data, customHeaders),
    
  delete: <T>(endpoint: string, customHeaders = {}) => 
    apiRequest<T>(endpoint, 'DELETE', null, customHeaders),
}; 