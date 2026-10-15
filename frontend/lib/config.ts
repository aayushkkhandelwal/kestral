/**
 * Global API configuration pointing to FastAPI backend
 */
export const API_BASE_URL =
  (process.env.NEXT_PUBLIC_API_URL ? process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, '') : '') ||
  (typeof window !== 'undefined'
    ? (window.location.protocol === 'https:' ? `${window.location.protocol}//${window.location.host}` : `http://${window.location.hostname}:8000`)
    : (process.env.BACKEND_URL ? process.env.BACKEND_URL.replace(/\/+$/, '') : 'http://localhost:8000'))

