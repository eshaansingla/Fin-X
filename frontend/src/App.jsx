import { useState } from 'react'
import { ThemeProvider } from './context/ThemeContext'
import AuthProvider, { useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import RadarPage from './pages/RadarPage'
import CardPage from './pages/CardPage'
import ChatPage from './pages/ChatPage'
import InshortsPage from './pages/InshortsPage'
import MarketWrapButton from './components/MarketWrapButton'
import WarmupBanner from './components/WarmupBanner'
import LandingPage from './pages/LandingPage'

function AppInner() {
  const { isAuthed } = useAuth()
  const [page, setPage]            = useState('radar')
  const [selectedSym, setSelected] = useState('')

  // Show landing page for unauthenticated users
  if (!isAuthed) {
    return <LandingPage onAuthed={() => setPage('radar')} />
  }

  const handleSelectStock = (symbol) => {
    setSelected(symbol)
    setPage('card')
  }

  const handleNav = (id) => {
    setPage(id)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 flex flex-col transition-colors duration-200">
      <Navbar active={page} onNav={handleNav} />
      <div className="max-w-6xl w-full mx-auto px-4">
        <WarmupBanner />
      </div>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
        {page === 'radar'    && <RadarPage onSelectStock={handleSelectStock} />}
        {page === 'card'     && <CardPage initialSym={selectedSym} />}
        {page === 'chat'     && <ChatPage />}
        {page === 'inshorts' && <InshortsPage onSelectStock={handleSelectStock} />}
      </main>
      <MarketWrapButton />
      <footer className="text-center text-xs text-gray-400 dark:text-gray-600 py-3 border-t border-gray-200 dark:border-gray-900">
        Fin-X — For educational purposes only. Not SEBI-registered investment advice. Data: NSE India
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppInner />
      </AuthProvider>
    </ThemeProvider>
  )
}
