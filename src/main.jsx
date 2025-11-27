import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'

import { AuthProvider } from './context/AuthContext.jsx'

import { BrowserRouter } from 'react-router-dom'

console.log("NEXUS v3.0 (Crash Proof) - Loaded");

// Global Error Handler
window.onerror = function (message, source, lineno, colno, error) {
  console.error("Global Error Caught:", message, error);
  // Optional: Send to analytics or show a toast if possible
  return false;
};

window.onunhandledrejection = function (event) {
  console.error("Unhandled Promise Rejection:", event.reason);
};

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </StrictMode>,
)
