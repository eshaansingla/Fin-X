import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, DollarSign, Gem, RefreshCw, AlertCircle } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const fmt  = (v) => v != null ? `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—'
const sign = (v) => v > 0 ? '+' : ''

const SECTIONS = [
  {
    key:   'gainers',
    label: 'Top Gainers',
    icon:  TrendingUp,
    colorCls: 'text-green-600 dark:text-green-500',
    borderCls: 'border-green-200 dark:border-green-900/40',
    bgCls: 'bg-green-50 dark:bg-green-950/20',
    badgeCls: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
  },
  {
    key:   'losers',
    label: 'Top Losers',
    icon:  TrendingDown,
    colorCls: 'text-red-600 dark:text-red-500',
    borderCls: 'border-red-200 dark:border-red-900/40',
    bgCls: 'bg-red-50 dark:bg-red-950/20',
    badgeCls: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400',
  },
  {
    key:   'cheapest',
    label: 'Cheapest',
    icon:  DollarSign,
    colorCls: 'text-blue-600 dark:text-blue-400',
    borderCls: 'border-blue-200 dark:border-blue-900/40',
    bgCls: 'bg-blue-50 dark:bg-blue-950/20',
    badgeCls: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400',
  },
  {
    key:   'expensive',
    label: 'Most Expensive',
    icon:  Gem,
    colorCls: 'text-purple-600 dark:text-purple-400',
    borderCls: 'border-purple-200 dark:border-purple-900/40',
    bgCls: 'bg-purple-50 dark:bg-purple-950/20',
    badgeCls: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-400',
  },
]

function MoverCard({ stock, badgeCls, onSelect }) {
  const isUp = (stock.change_pct ?? 0) >= 0
  return (
    <button
      onClick={() => onSelect?.(stock.symbol)}
      className="flex-shrink-0 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700
        rounded-xl p-3 text-left hover:border-blue-300 dark:hover:border-blue-600
        hover:shadow-md transition-all duration-150 cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-1.5">
        <span className="text-xs font-bold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
          {stock.symbol}
        </span>
        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${badgeCls}`}>
          {sign(stock.change_pct)}{stock.change_pct != null ? stock.change_pct.toFixed(2) : '—'}%
        </span>
      </div>
      <p className="text-[10px] text-gray-400 truncate mb-2 leading-tight">{stock.name}</p>
      <p className="text-sm font-bold text-gray-900 dark:text-gray-100">{fmt(stock.price)}</p>
    </button>
  )
}

function SectionRow({ section, stocks, onSelect }) {
  const Icon = section.icon
  if (!stocks || stocks.length === 0) return null

  return (
    <div className={`rounded-2xl border ${section.borderCls} ${section.bgCls} p-4`}>
      <div className="flex items-center gap-2 mb-3">
        <Icon className={`w-4 h-4 ${section.colorCls} flex-shrink-0`} />
        <h3 className={`text-sm font-bold ${section.colorCls}`}>{section.label}</h3>
        <span className="text-xs text-gray-400 ml-auto">{stocks.length} stocks</span>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
        {stocks.map(stock => (
          <MoverCard
            key={stock.symbol}
            stock={stock}
            badgeCls={section.badgeCls}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  )
}

export default function MarketMovers({ onSelectStock }) {
  const [data,     setData]     = useState(null)
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)
  const [lastFetch, setLast]    = useState(null)

  const fetchMovers = async (silent = false) => {
    if (!silent) setLoading(true)
    setError(null)
    try {
      const res  = await fetch(`${API_BASE}/market/movers`)
      const json = await res.json()
      if (json.success && json.data) {
        setData(json.data)
        setLast(new Date())
      } else {
        setError(json.error || 'Failed to load movers')
      }
    } catch (e) {
      setError('Network error — check if backend is running')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMovers()
    // Refresh every 60 seconds
    const t = setInterval(() => fetchMovers(true), 60_000)
    return () => clearInterval(t)
  }, [])

  if (loading && !data) {
    return (
      <div className="space-y-3">
        <div className="h-6 w-48 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[1,2,3,4].map(i => (
            <div key={i} className="h-28 bg-gray-100 dark:bg-gray-800 rounded-2xl animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-400 bg-gray-100 dark:bg-gray-800/50 rounded-xl p-3 border border-gray-200 dark:border-gray-700">
        <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0" />
        <span>{error}</span>
        <button onClick={() => fetchMovers()} className="ml-auto text-blue-600 dark:text-blue-400 hover:underline text-xs">Retry</button>
      </div>
    )
  }

  if (!data) return null

  const hasAny = SECTIONS.some(s => data[s.key]?.length > 0)
  if (!hasAny) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-gray-900 dark:text-white">Market Movers</h2>
          {lastFetch && (
            <p className="text-xs text-gray-400 mt-0.5">
              {data.total} stocks · updated {lastFetch.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
            </p>
          )}
        </div>
        <button
          onClick={() => fetchMovers(false)}
          disabled={loading}
          className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {SECTIONS.map(section => (
          <SectionRow
            key={section.key}
            section={section}
            stocks={data[section.key]}
            onSelect={onSelectStock}
          />
        ))}
      </div>
    </div>
  )
}
