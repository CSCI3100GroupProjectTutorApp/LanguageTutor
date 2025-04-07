// Authentication types
interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Token storage
let authToken: string | null = null;

// Token management functions
export const getAuthToken = async (): Promise<string | null> => {
  return authToken;
};

export const setAuthToken = (token: string): void => {
  authToken = token;
};

export const clearAuthToken = (): void => {
  authToken = null;
};

export const isAuthenticated = (): boolean => {
  return !!authToken;
}; 