import { useState, useEffect, useCallback } from 'react'
import SignalFeed from '../components/SignalFeed'
import ClusterRadar from '../components/ClusterRadar'
import MarketMovers from '../components/MarketMovers'
import { fetchSignals, refreshRadar } from '../api'

const REFRESH_MS = 60_000

export default function RadarPage({ onSelectStock }) {
  const [signals,     setSignals]  = useState([])
  const [loading,     setLoading]  = useState(false)
  const [lastUpdated, setLast]     = useState(null)

  const load = useCallback(async () => {
    try {
      const data = await fetchSignals({ limit: 30 })
      setSignals(data.signals || [])
      setLast(new Date().toISOString())
    } catch (e) {
      console.error('[Radar]', e.message)
    }
  }, [])

  const handleRefresh = async () => {
    setLoading(true)
    try { await refreshRadar(); await load() }
    catch (e) { console.error('[Refresh]', e.message) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    load()
    const t = setInterval(load, REFRESH_MS)
    return () => clearInterval(t)
  }, [load])

  return (
    <div className="space-y-6">
      {/* Market Movers — gainers, losers, cheapest, expensive */}
      <MarketMovers onSelectStock={onSelectStock} />

      {/* Institutional cluster intelligence */}
      <ClusterRadar />

      {/* AI-explained bulk deal signals */}
      <SignalFeed
        signals={signals}
        loading={loading}
        onRefresh={handleRefresh}
        lastUpdated={lastUpdated}
      />
    </div>
  )
}
