/**
 * Capacitor shell — install @capacitor/core + CLI when packaging the mobile WebView.
 * Point `server.url` at the deployed Nuxt origin (same Store/public routes).
 *
 * Production (Phase 8 default): https://as.hindupanjang.com
 * Local WebView:
 *   CAPACITOR_SERVER_URL=http://localhost:3001 CAPACITOR_CLEARTEXT=true
 */
const serverUrl = process.env.CAPACITOR_SERVER_URL || 'https://as.hindupanjang.com'
const cleartext = process.env.CAPACITOR_CLEARTEXT === 'true' || serverUrl.startsWith('http://')

const config = {
  appId: 'com.asorganic.app',
  appName: 'AS Organic',
  webDir: 'dist',
  server: {
    url: serverUrl,
    cleartext
  }
}

export default config
