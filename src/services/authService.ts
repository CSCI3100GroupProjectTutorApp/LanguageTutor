// Authentication types
interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Token storage
let authToken: string | null = null;

// Login function
export const login = async (username: string, password: string): Promise<string> => {
  try {
    const response = await fetch('http://localhost:8000/login', {
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
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data: LoginResponse = await response.json();
    // Store the token
    authToken = data.access_token;
    return data.access_token;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

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