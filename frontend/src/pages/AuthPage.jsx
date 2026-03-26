import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function AuthPage({ onAuthed }) {
  const { login, register, isAuthed } = useAuth()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e?.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = { email, password }
      if (mode === 'register') {
        await register(payload)
      } else {
        await login(payload)
      }
      onAuthed?.()
    } catch (err) {
      setError(err?.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthed) onAuthed?.()
  }, [isAuthed, onAuthed])

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

