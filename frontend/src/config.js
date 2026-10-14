/**
 * Global API configuration that dynamically adapts to localhost or LAN mobile IP
 */
export const API_BASE_URL = typeof window !== 'undefined'
  ? `http://${window.location.hostname}:8000`
  : 'http://localhost:8000';
