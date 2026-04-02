import { useState, useEffect, useCallback } from 'react'

/**
 * Convert a base64 URL-safe string to a Uint8Array for the push subscription.
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

type PermissionState = 'prompt' | 'granted' | 'denied' | 'unsupported'

export function NotificationPrompt() {
  const [permState, setPermState] = useState<PermissionState>('prompt')
  const [subscribed, setSubscribed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (!('Notification' in window) || !('serviceWorker' in navigator)) {
      setPermState('unsupported')
      return
    }
    setPermState(Notification.permission as PermissionState)

    // Check if already subscribed
    navigator.serviceWorker.ready.then((reg) => {
      reg.pushManager.getSubscription().then((sub) => {
        if (sub) setSubscribed(true)
      })
    })

    // Check if user previously dismissed
    if (localStorage.getItem('tendril-notif-dismissed') === 'true') {
      setDismissed(true)
    }
  }, [])

  const handleEnable = useCallback(async () => {
    setLoading(true)
    try {
      // Request permission
      const permission = await Notification.requestPermission()
      setPermState(permission as PermissionState)

      if (permission !== 'granted') {
        setLoading(false)
        return
      }

      // Get VAPID public key
      const keyRes = await fetch('/api/push/vapid-public-key')
      if (!keyRes.ok) {
        console.warn('Push not configured on server')
        setLoading(false)
        return
      }
      const { public_key } = await keyRes.json()

      // Subscribe to push
      const reg = await navigator.serviceWorker.ready
      const subscription = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(public_key),
      })

      // Send subscription to backend
      const subJson = subscription.toJSON()
      const res = await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: subJson.endpoint,
          p256dh_key: subJson.keys?.p256dh || '',
          auth_key: subJson.keys?.auth || '',
        }),
      })

      if (res.ok) {
        setSubscribed(true)
      }
    } catch (err) {
      console.error('Failed to enable notifications:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleDismiss = () => {
    setDismissed(true)
    localStorage.setItem('tendril-notif-dismissed', 'true')
  }

  // Don't show if unsupported, already granted, denied, or dismissed
  if (
    permState === 'unsupported' ||
    permState === 'denied' ||
    subscribed ||
    dismissed
  ) {
    return null
  }

  return (
    <div className="notification-prompt">
      <div className="notification-prompt-content">
        <span className="notification-prompt-icon">🔔</span>
        <div className="notification-prompt-text">
          <strong>Enable notifications?</strong>
          <p>Get reminders for watering, harvesting, and planting tasks.</p>
        </div>
      </div>
      <div className="notification-prompt-actions">
        <button
          className="btn btn-primary btn-sm"
          onClick={handleEnable}
          disabled={loading}
        >
          {loading ? 'Enabling…' : 'Enable'}
        </button>
        <button
          className="btn btn-outline btn-sm"
          onClick={handleDismiss}
        >
          Not now
        </button>
      </div>
    </div>
  )
}
