import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../api'

export default function AuthPage({ onAuthed }) {
  const { login, register, isAuthed } = useAuth()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [checkEmail, setCheckEmail] = useState(false)
  const [emailSent, setEmailSent] = useState(true)
  const [fallbackLink, setFallbackLink] = useState('')
  const [verifyStatus, setVerifyStatus] = useState(null) // 'ok' | 'fail' | null

  // Handle ?verify=<token> in URL on page load
  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('verify')
    if (!token) return
    // Clear the token from the URL without reload
    window.history.replaceState({}, '', window.location.pathname)
    api.get(`/auth/verify/${token}`)
      .then(() => setVerifyStatus('ok'))
      .catch(() => setVerifyStatus('fail'))
  }, [])

  const submit = async (e) => {
    e?.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = { email, password }
      if (mode === 'register') {
        const res = await register(payload)
        setEmailSent(res?.email_sent !== false)
        setFallbackLink(res?.verification_link || '')
        setCheckEmail(true)
      } else {
        await login(payload)
        onAuthed?.()
      }
    } catch (err) {
      setError(err?.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthed) onAuthed?.()
  }, [isAuthed, onAuthed])

  if (verifyStatus === 'ok') {
    return (
      <div className="max-w-md mx-auto">
        <div className="rounded-lg border border-green-200 bg-white dark:bg-gray-900 dark:border-green-800 p-6">
          <div className="text-lg font-semibold text-green-600 mb-1">Email verified!</div>
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">Your account is now active. You can log in.</div>
          <button
            onClick={() => setVerifyStatus(null)}
            className="text-sm text-blue-600 underline"
          >
            Go to login
          </button>
        </div>
      </div>
    )
  }

  if (verifyStatus === 'fail') {
    return (
      <div className="max-w-md mx-auto">
        <div className="rounded-lg border border-red-200 bg-white dark:bg-gray-900 dark:border-red-800 p-6">
          <div className="text-lg font-semibold text-red-600 mb-1">Invalid link</div>
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">This verification link is invalid or has already been used.</div>
          <button
            onClick={() => setVerifyStatus(null)}
            className="text-sm text-blue-600 underline"
          >
            Back to login
          </button>
        </div>
      </div>
    )
  }

  if (checkEmail) {
    return (
      <div className="max-w-md mx-auto">
        <div className="rounded-lg border border-blue-200 bg-white dark:bg-gray-900 dark:border-blue-800 p-6">
          <div className="text-lg font-semibold mb-1">Check your email</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {emailSent ? (
              <>
                We sent a verification link to <span className="font-medium text-gray-700 dark:text-gray-200">{email}</span>.
                Click the link to activate your account, then come back to log in.
              </>
            ) : (
              <>
                SMTP is not configured, so email was not sent. Use the verification link below for local testing.
              </>
            )}
          </div>
          {!emailSent && fallbackLink && (
            <div className="mt-3 p-2 rounded bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-xs break-all text-gray-700 dark:text-gray-200">
              {fallbackLink}
            </div>
          )}
          <button
            onClick={() => { setCheckEmail(false); setMode('login') }}
            className="mt-4 text-sm text-blue-600 underline"
          >
            Back to login
          </button>
        </div>
      </div>
    )
  }

  if (isAuthed) {
    return (
      <div className="max-w-md mx-auto">
        <div className="rounded-lg border border-gray-200 bg-white dark:bg-gray-900 dark:border-gray-800 p-6">
          <div className="text-lg font-semibold mb-1">Logged in</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Redirecting...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="rounded-lg border border-gray-200 bg-white dark:bg-gray-900 dark:border-gray-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-lg font-semibold">FIN-X Account</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Email + password</div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setMode('login')}
              className={`text-xs px-3 py-1.5 rounded-lg border ${
                mode === 'login'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-transparent text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setMode('register')}
              className={`text-xs px-3 py-1.5 rounded-lg border ${
                mode === 'register'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-transparent text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700'
              }`}
            >
              Register
            </button>
          </div>
        </div>

        <form onSubmit={submit} className="space-y-3">
          <label className="text-sm block">
            <div className="text-gray-600 dark:text-gray-300 mb-1">Email</div>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20"
              required
            />
          </label>
          <label className="text-sm block">
            <div className="text-gray-600 dark:text-gray-300 mb-1">Password</div>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20"
              required
              minLength={8}
            />
          </label>

          {error && <div className="text-sm text-red-600">{error}</div>}

          <button
            type="submit"
            disabled={loading || !email || !password}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-gray-300 dark:disabled:bg-gray-800 text-white rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors"
          >
            {loading ? 'Please wait...' : mode === 'register' ? 'Create account' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  )
}

