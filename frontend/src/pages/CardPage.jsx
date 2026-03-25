import { useState, useEffect, useRef, useCallback } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import SignalCard from '../components/SignalCard'
import SearchBar from '../components/SearchBar'
import { fetchSignalCard } from '../api'
import { RefreshCw, Wifi } from 'lucide-react'

// Fixed: removed stray comma that caused undefined entry
const POPULAR = [
  'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
  'WIPRO', 'BAJFINANCE', 'SUNPHARMA', 'ITC',
]

const TREND_KEYS = { '1D': '1d', '1W': '1w', '1M': '1m' }
const TREND_LABEL = { '1D': 'Intraday', '1W': '5 Days', '1M': '30 Days' }

// ── Trend Chart ──────────────────────────────────────────────
function TrendChart({ trends }) {
  const [tab, setTab] = useState('1M')
  if (!trends) return null

  const raw = trends[TREND_KEYS[tab]] || []
  const data = raw.map(d => ({ ...d, price: Number(d.price) }))

  const hasData = data.length >= 2
  const first = hasData ? data[0].price : 0
  const last = hasData ? data[data.length - 1].price : 0
  const isUp = last >= first
  const pctMove = first ? (((last - first) / first) * 100).toFixed(2) : null
  const color = isUp ? '#10b981' : '#ef4444'

  const fmtTick = (v) => {
    if (!v) return ''
    const s = String(v)
    const d = new Date(s)
    if (isNaN(d)) return s.slice(-5)
    if (s.includes('T') || (s.includes(':') && !s.includes('-'))) {
      return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })
    }
    return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
  }

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 shadow-sm dark:shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-sm font-semibold text-gray-900 dark:text-white">Price Trend</p>
          {hasData && pctMove !== null && (
            <p className={`text-xs font-semibold mt-0.5 ${isUp ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}`}>
              {isUp ? '▲ +' : '▼ '}{pctMove}% · {TREND_LABEL[tab]}
            </p>
          )}
        </div>
        <div className="flex gap-0.5 bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5 border border-gray-200 dark:border-gray-700">
          {['1D', '1W', '1M'].map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-150
                ${tab === t
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {hasData ? (
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
            <XAxis
              dataKey="time"
              tick={{ fill: '#9ca3af', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
              tickFormatter={fmtTick}
            />
            <YAxis hide domain={['auto', 'auto']} />
            <Tooltip
              content={({ payload, label }) =>
                payload?.[0] ? (
                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 shadow-xl text-xs">
                    <p className="text-gray-500 mb-0.5">{label}</p>
                    <p className="text-gray-900 dark:text-white font-bold">
                      ₹{Number(payload[0].value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                ) : null
              }
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: color, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-[180px] flex items-center justify-center text-gray-400 text-sm">
          No {tab} data available
        </div>
      )}
    </div>
  )
}

// ── Loading skeleton ─────────────────────────────────────────
function Skeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 h-56" />
      <div className="bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 space-y-4">
        <div className="h-7 bg-gray-200 dark:bg-gray-800 rounded w-36" />
        <div className="h-5 bg-gray-200 dark:bg-gray-800 rounded w-52" />
        <div className="grid grid-cols-4 gap-2">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-12 bg-gray-200 dark:bg-gray-800 rounded-xl" />)}
        </div>
        <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-full" />
        <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-4/5" />
        <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-3/5" />
      </div>
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────
export default function CardPage({ initialSym = '' }) {
  const [sym, setSym] = useState('')
  const [card, setCard] = useState(null)
  const [loading, setLoad] = useState(false)
  const [silentLoad, setSilent] = useState(false)
  const [error, setError] = useState(null)
  const pollRef = useRef(null)

  const load = useCallback(async (ticker, silent = false, forceRefresh = false) => {
    if (!ticker) return
    if (silent) setSilent(true)
    else { setLoad(true); setCard(null); setError(null) }
    try {
      const data = await fetchSignalCard(ticker, forceRefresh || silent)
      setCard(data.card)
      if (!silent) setSym(ticker)
      setError(null)
    } catch (e) {
      if (!silent) setError(`Could not load ${ticker}: ${e.message}`)
    } finally {
      setLoad(false)
      setSilent(false)
    }
  }, [])

  // Auto-load when navigated here from MarketMovers or other external source
  useEffect(() => {
    if (initialSym) {
      clearInterval(pollRef.current)
      load(initialSym, false)
    }
  }, [initialSym, load])

  // 30s silent poll for live price updates
  useEffect(() => {
    if (!sym) return
    clearInterval(pollRef.current)
    pollRef.current = setInterval(() => load(sym, true), 30_000)
    return () => clearInterval(pollRef.current)
  }, [sym, load])

  // handleSelect: clear polling, set sym immediately, then load
  const handleSelect = (ticker) => {
    if (!ticker) return
    clearInterval(pollRef.current)
    setSym(ticker)
    load(ticker, false)
  }

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">NSE Signal Card</h2>
          <p className="text-sm text-gray-500 mt-0.5">AI-powered stock analysis · Live NSE data</p>
        </div>
        {card && !loading && (
          <div className="flex items-center gap-2">
            {silentLoad && (
              <span className="flex items-center gap-1.5 text-xs text-gray-400">
                <Wifi className="w-3 h-3 animate-pulse text-green-500" />
                Live
              </span>
            )}
            <button
              onClick={() => load(sym, false, true)}
              title="Force refresh"
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Smart search */}
      <SearchBar onSelect={handleSelect} />

      {/* Popular stocks */}
      <div className="flex flex-wrap gap-2">
        {POPULAR.filter(Boolean).map(s => (
          <button
            key={s}
            onClick={() => handleSelect(s)}
            className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-all duration-150
              ${sym === s
                ? 'bg-blue-600 border-blue-500 text-white shadow-sm'
                : 'bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-blue-400 dark:hover:border-blue-600 hover:text-gray-900 dark:hover:text-white'
              }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* States */}
      {loading && <Skeleton />}

      {error && !loading && (
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-xl p-4 flex items-center justify-between">
          <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          <button
            onClick={() => load(sym, false)}
            className="text-xs text-red-600 dark:text-red-400 hover:underline ml-3 flex-shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && !card && (
        <div className="text-center py-20 text-gray-400">
          <p className="text-sm">Search for a stock or click a popular ticker above</p>
        </div>
      )}

      {/* Chart + Card */}
      {card && !loading && (
        <div className="space-y-4">
          <TrendChart trends={card.trends} />
          <SignalCard card={card} />
        </div>
      )}
    </div>
  )
}
