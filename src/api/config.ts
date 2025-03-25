/**
 * API configuration for the language tutoring application
 * This file contains the base URL and other configurations for API requests
 */

// Base API URL - adjust based on your development/production environment
export const API_BASE_URL = 'http://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  LOGIN: '/login',
  REGISTER: '/register',
  REFRESH_TOKEN: '/refresh-token',
  LOGOUT: '/logout',
  
  // User endpoints
  USER_PROFILE: '/user/profile',
  USER_WORDS: '/user/words',
  
  // Database test
  TEST_DB: '/test-db',
};

// Default request headers
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
};

// Timeout for API requests in milliseconds
export const REQUEST_TIMEOUT = 15000; // 15 seconds 