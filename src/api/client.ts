/**
 * API client for the language tutoring application
 * Handles API requests to the backend
 */
import { API_BASE_URL, DEFAULT_HEADERS, REQUEST_TIMEOUT } from './config';

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

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
    mode: 'cors'
  };
  
  if (data) {
    if (headers['Content-Type'] === 'application/x-www-form-urlencoded') {
      options.body = data;
    } else if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
      options.body = JSON.stringify(data);
    }
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
    
    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.indexOf('application/json') !== -1;
    const responseData = isJson ? await response.json() : await response.text();
    
    if (!response.ok || responseData?.error || 
        (typeof responseData === 'string' && responseData.includes('already exists'))) {
      // Try to extract error message
      let errorMessage = '';
      if (typeof responseData === 'string') {
        errorMessage = responseData;
      } else if (responseData?.detail) {
        errorMessage = Array.isArray(responseData.detail) 
          ? responseData.detail.map((err: any) => err.msg).join(', ')
          : responseData.detail;
      } else if (responseData?.message) {
        errorMessage = responseData.message;
      } else if (responseData?.error) {
        errorMessage = responseData.error;
      } else {
        errorMessage = `API error: ${response.status} ${response.statusText}`;
      }
      
      throw new APIError(
        errorMessage,
        response.status,
        responseData
      );
    }
    
    return responseData as T;
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