import {Info} from '../../assets/types/UserInfo'


// Authentication types
interface LoginResponse {
    access_token: string;
    token_type: string;
  }
  
  // Token storage
  let authToken: string | null = null;
  let refreshToken: string | null = null;
  const API_BASE_URL = 'http://192.168.0.118:8000';
  
  // Token management functions
  export const getAuthToken = async (): Promise<string | null> => {
    /*
    if (!authToken){
      try{
        const response = await fetch(`${API_BASE_URL}/refresh-token`,{
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(refreshToken)

        })
        if (!response.ok) {
          throw new Error(`Getting userid failed with status: ${response.status}`);
        }
        const data = await response.json();
        authToken = data.access_token
        refreshToken = data.refresh_token
      } 
      catch (e){
        console.error('Error in refreshing token:', e);
      }
    }
    */
    return authToken      
  };
  export const setRefreshToken = (token: string):void => {
    refreshToken = token;
  }

  export const setAuthToken = (token: string): void => {
    authToken = token;
  };
  
  export const clearAuthToken = (): void => {
    authToken = null;
  };
  
  export const isAuthenticated = (): boolean => {
    return !!authToken;
  }; 

  export const getUserID = async (): Promise<string | null> => {
    try{
      const token = getAuthToken()
      if (!token) {
        throw new Error('Not authenticated');
      }
      console.log(token)
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token._j}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) {
        throw new Error(`Getting userid failed with status: ${response.status}`);
      }
  
      const data = await response.json();
      return data.user_id
    }
    catch (e){
      console.error('Error in getting userid:', e);
    }
    return null;
  };

  export const getUserInfo = async (): Promise<Info | null> => {
    try{
      const token = getAuthToken()
      if (!token) {
        throw new Error('Not authenticated');
      }
      console.log(token)
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token._j}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) {
        throw new Error(`Getting userid failed with status: ${response.status}`);
      }
  
      const data = await response.json();
      return {
        username:data.username,
        email: data.email,
        lastLogin: data.last_login,
        created: data.created_at,
      }
    }
    catch (e){
      console.error('Error in getting userid:', e);
    }
    return null;
  };