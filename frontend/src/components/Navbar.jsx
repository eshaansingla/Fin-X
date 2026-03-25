import { Activity, BarChart2, MessageSquare, Newspaper, Sun, Moon } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

const TABS = [
  { id: 'radar', label: 'Radar',       icon: Activity },
  { id: 'card',  label: 'Signal Card', icon: BarChart2 },
  { id: 'inshorts', label: 'Inshorts', icon: Newspaper },
  { id: 'chat',  label: 'Market Chat', icon: MessageSquare },
]

export default function Navbar({ active, onNav }) {
  const { dark, toggle } = useTheme()

  return (
    <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between gap-4">

        {/* Logo */}
        <div className="flex items-center gap-2.5 flex-shrink-0">
          <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-md">
            <span className="text-white text-xs font-extrabold tracking-tight">FX</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-gray-900 dark:text-white text-lg tracking-tight">Fin-X</span>
            <span className="text-gray-400 dark:text-gray-600 text-xs hidden sm:block border-l border-gray-200 dark:border-gray-700 pl-2">
              NSE Intelligence
            </span>
          </div>
        </div>

        {/* Nav tabs */}
        <div className="flex items-center gap-1 flex-1 justify-center">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => onNav(id)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150
                ${active === id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="hidden md:inline">{label}</span>
            </button>
          ))}
        </div>

        {/* Theme toggle */}
        <button
          onClick={toggle}
          title={dark ? 'Switch to Light mode' : 'Switch to Dark mode'}
          className="flex-shrink-0 p-2 rounded-lg text-gray-500 dark:text-gray-400
            hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800
            transition-colors duration-150"
        >
          {dark
            ? <Sun  className="w-4 h-4" />
            : <Moon className="w-4 h-4" />
          }
        </button>
      </div>
    </nav>
  )
}
