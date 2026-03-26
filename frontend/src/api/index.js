import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
})

// Fast client for price-only endpoints — short timeout, no retry wait
const fastApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 5000,
})

let _authToken = null

export const setAuthToken = (token) => {
  _authToken = token
}

export const getAuthToken = () => _authToken

const _unwrap = r => {
  const body = r.data
  if (body && typeof body === 'object' && 'success' in body) {
    if (!body.success) return Promise.reject(new Error(body.error || 'Request failed'))
    return body.data
  }
  return body
}
const _onErr = err => {
  const msg = err.response?.data?.error
         || err.response?.data?.detail
         || err.message
         || 'Network error'
  return Promise.reject(new Error(msg))
}

api.interceptors.response.use(_unwrap, _onErr)
fastApi.interceptors.response.use(_unwrap, _onErr)

api.interceptors.request.use((config) => {
  if (_authToken) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${_authToken}`
  }
  return config
})

fastApi.interceptors.request.use((config) => {
  if (_authToken) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${_authToken}`
  }
  return config
})

export const fetchSignals      = (p = {})   => api.get('/signals', { params: p })
export const refreshRadar      = ()         => api.post('/signals/refresh')
export const fetchSignalCard   = (sym, fr)  => api.get(`/card/${sym}`, { params: { force_refresh: fr } })
export const sendChatMessage   = (msg, sid) => api.post('/chat', { message: msg, session_id: sid || null })
export const clearChat         = (sid)      => api.delete(`/chat/${sid}`)
export const pingHealth        = ()         => api.get('/health')
export const searchStocks      = (q)        => api.get('/search', { params: { q } })
export const fetchMarketMovers = ()         => api.get('/market/movers')
export const fetchInshorts     = (force)    => api.get('/inshorts', { params: { force_refresh: force || false } })
export const fetchMarketStatus = ()         => api.get('/market/status')
export const fetchLiveQuote    = (sym)      => api.get(`/market/live/${sym}`)
export const fetchMarketChart  = (sym, p)   => api.get(`/market/chart/${sym}`, { params: { period: p } })
// Ultra-fast price-only fetch (no intraday chart) — for instant first render
export const fetchQuickPrice   = (sym)      => fastApi.get(`/market/price/${sym}`)

export const getMarketWsUrl = (sym) => {
  const base = import.meta.env.VITE_API_URL || '/api'
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  const isAbs = /^https?:\/\//i.test(base)
  const httpBase = isAbs ? base : `${origin}${base}`
  const wsBase = httpBase.replace(/^http:/i, 'ws:').replace(/^https:/i, 'wss:')
  return `${wsBase}/market/ws/${encodeURIComponent(sym)}`
}

// Export the raw axios instances for auth flows (token-aware via interceptors).
export { api, fastApi }
