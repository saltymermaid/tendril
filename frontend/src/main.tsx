import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { disableAutofillPrompts } from './lib/disableAutofillPrompts'
import './index.css'

// Suppress Dashlane/password-manager autofill icons on all form fields app-wide
disableAutofillPrompts()

// Register service worker for PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((reg) => {
        console.log('SW registered:', reg.scope)
      })
      .catch((err) => {
        console.warn('SW registration failed:', err)
      })
  })
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
