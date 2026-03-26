import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'
import { AlertTriangle, TrendingUp, TrendingDown, Minus, ExternalLink, BarChart3 } from 'lucide-react'
import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const SENTIMENT = {
  bullish: {
    label: 'Bullish',
    textCls: 'text-emerald-600 dark:text-emerald-400',
    bgCls:   'bg-emerald-50 border border-emerald-200 dark:bg-emerald-900/30 dark:border-emerald-700/50',
    icon: TrendingUp,
  },
  bearish: {
    label: 'Bearish',
    textCls: 'text-red-600 dark:text-red-400',
    bgCls:   'bg-red-50 border border-red-200 dark:bg-red-900/30 dark:border-red-700/50',
    icon: TrendingDown,
  },
  neutral: {
    label: 'Neutral',
    textCls: 'text-amber-600 dark:text-amber-400',
    bgCls:   'bg-amber-50 border border-amber-200 dark:bg-amber-900/30 dark:border-amber-700/50',
    icon: Minus,
  },
}

const fmt    = (v) => v != null ? `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—'
const fmtNum = (v) => v != null ? Number(v).toLocaleString('en-IN') : '—'

function MiniChart({ prices = [], changePct = 0 }) {
  if (!prices || prices.length < 2) return null
  const isUp = (changePct ?? 0) >= 0
  const data = prices.map((v, i) => ({ i, v: Number(v) }))
  return (
    <ResponsiveContainer width="100%" height={60}>
      <LineChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <Line type="monotone" dataKey="v" stroke={isUp ? '#10b981' : '#ef4444'} strokeWidth={1.5} dot={false} />
        <Tooltip
          content={({ payload }) =>
            payload?.[0] ? (
              <div className="bg-white dark:bg-gray-800 text-xs px-2 py-1 rounded border border-gray-200 dark:border-gray-700 shadow-lg">
                {fmt(payload[0].value)}
              </div>
            ) : null
          }
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

function StatBox({ label, value, cls = '' }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800/70 rounded-xl px-3 py-2.5 border border-gray-100 dark:border-gray-700/30">
      <p className="text-gray-500 dark:text-gray-500 text-[10px] uppercase tracking-wider font-semibold mb-1">{label}</p>
      <p className={`font-semibold text-sm ${cls || 'text-gray-900 dark:text-gray-100'}`}>{value}</p>
    </div>
  )
}

export default function SignalCard({ card }) {
  const [winRate, setWinRate] = useState(null) // { pct, n } | null

  useEffect(() => {
    if (!card?.symbol) return
    fetch(`${API_BASE}/analytics/success-rate/${card.symbol}?signal_type=${encodeURIComponent(card.ema_signal || 'EMA Crossover')}`)
      .then(r => r.json())
      .then(d => {
        if (d.win_rate != null) setWinRate({ pct: d.win_rate, n: d.occurrences ?? null })
      })
      .catch(() => {})
  }, [card?.symbol, card?.ema_signal])

  if (!card) return null

  const s    = SENTIMENT[card.sentiment] || SENTIMENT.neutral
  const Icon = s.icon
  const isUp = (card.change_pct ?? 0) >= 0

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 space-y-5 relative shadow-sm dark:shadow-xl">

      {/* Win rate badge */}
      {winRate != null && (
        <div className="absolute top-4 right-4 bg-gradient-to-r from-indigo-600 to-purple-600
          text-white text-xs font-bold px-2.5 py-1 rounded-full shadow border border-purple-500/30 flex items-center gap-1">
          ★ {winRate.pct}% Win
          {winRate.n != null && winRate.n > 0 && (
            <span className="opacity-70 font-normal">· {winRate.n} signals</span>
          )}
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <h2 className="text-2xl font-extrabold text-gray-900 dark:text-white tracking-tight">{card.symbol}</h2>
            <span className="text-xs text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full border border-gray-200 dark:border-gray-700">NSE</span>
          </div>
          {card.current_price != null && (
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                ₹{Number(card.current_price).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </span>
              <span className={`text-sm font-semibold ${isUp ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}`}>
                {isUp ? '▲ +' : '▼ '}{card.change_pct != null ? card.change_pct : '—'}%
              </span>
            </div>
          )}
        </div>
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold flex-shrink-0 ${s.bgCls} ${s.textCls}`}>
          <Icon className="w-3.5 h-3.5" />
          {s.label}
          {card.sentiment_score != null && (
            <span className="text-xs opacity-60">· {card.sentiment_score}</span>
          )}
        </div>
      </div>

      {/* Mini chart */}
      {card.price_30d?.length >= 2 && (
        <MiniChart prices={card.price_30d} changePct={card.change_pct} />
      )}

      {/* OHLC grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <StatBox label="Open"       value={fmt(card.open)} />
        <StatBox label="High"       value={fmt(card.high)}       cls="text-green-600 dark:text-green-500" />
        <StatBox label="Low"        value={fmt(card.low)}        cls="text-red-600 dark:text-red-500" />
        <StatBox label="Prev Close" value={fmt(card.prev_close)} />
      </div>
      {card.volume != null && (
        <div className="bg-gray-50 dark:bg-gray-800/70 border border-gray-100 dark:border-gray-700/30 rounded-xl px-4 py-2.5 flex items-center justify-between">
          <p className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold">Volume</p>
          <p className="font-semibold text-sm text-gray-900 dark:text-gray-100">{fmtNum(card.volume)}</p>
        </div>
      )}

      {/* Technical Snapshot */}
      <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/20 rounded-xl p-4 space-y-2">
        <div className="flex items-center gap-2 mb-1">
          <BarChart3 className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Technical Snapshot</p>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{card.technical_snapshot || '—'}</p>
        {(card.rsi != null || card.ema_signal) && (
          <div className="flex flex-wrap gap-2 pt-1 text-xs">
            {card.rsi != null && (
              <span className="bg-gray-200 dark:bg-gray-700/60 text-gray-700 dark:text-gray-300 rounded-lg px-2.5 py-1">
                RSI <span className="font-semibold ml-1">{card.rsi}</span>
                {card.rsi_zone && (
                  <span className="text-gray-500 ml-1 capitalize">({card.rsi_zone.replace('_', ' ')})</span>
                )}
              </span>
            )}
            {card.ema_signal && (
              <span className="bg-gray-200 dark:bg-gray-700/60 text-gray-700 dark:text-gray-300 rounded-lg px-2.5 py-1">
                EMA <span className="font-semibold ml-1 capitalize">{card.ema_signal.replace('_', ' ')}</span>
              </span>
            )}
          </div>
        )}
      </div>

      {/* News Impact — hidden when AI returned the fallback */}
      {card.news_impact_summary && card.news_impact_summary !== 'News data unavailable.' && (
        <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/20 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">News Impact</p>
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-24 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    (card.news_impact_score ?? 50) >= 60 ? 'bg-green-500' :
                    (card.news_impact_score ?? 50) >= 40 ? 'bg-amber-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${card.news_impact_score ?? 50}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 tabular-nums">{card.news_impact_score ?? '—'}/100</span>
            </div>
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{card.news_impact_summary}</p>
        </div>
      )}

      {/* Risk Flags */}
      {card.risk_flags?.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Risk Flags</p>
          <div className="space-y-1.5">
            {card.risk_flags.map((flag, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/20 rounded-lg px-3 py-2 border border-amber-100 dark:border-amber-900/20">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
                <span>{flag}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actionable Context */}
      {card.actionable_context && (
        <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800/30 rounded-xl p-4">
          <p className="text-sm text-blue-700 dark:text-blue-200 leading-relaxed">{card.actionable_context}</p>
        </div>
      )}

      {/* News Links — hidden when empty */}
      {card.news?.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold mb-2">Recent News</p>
          <div className="divide-y divide-gray-100 dark:divide-gray-800/60">
            {card.news.map((n, i) => (
              <a
                key={i}
                href={n.url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-2 py-2.5 text-xs text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 leading-relaxed transition-colors group"
              >
                <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
                <span>{n.headline}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-xs text-gray-400 dark:text-gray-600 border-t border-gray-100 dark:border-gray-800 pt-3 leading-relaxed">
        {card.disclaimer || 'For educational purposes only. Not SEBI-registered investment advice.'}
      </p>
    </div>
  )
}
