/**
 * API module index
 * Exports all API functionality
 */

export * from './client';
export * from './config';
export * from './auth';

// Re-export common types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
} 