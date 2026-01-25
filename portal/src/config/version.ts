// Version is injected at build time via VITE_APP_VERSION environment variable
// Falls back to 'dev' in development mode
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || 'dev'
