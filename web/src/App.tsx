import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { MapPage } from './pages/MapPage'
import { HotspotsPage } from './pages/HotspotsPage'
import { ValidationPage } from './pages/ValidationPage'
import { MethodPage } from './pages/MethodPage'

// ---------------------------------------------------------------------------
// Nav
// ---------------------------------------------------------------------------

const NAV_ITEMS: { to: string; label: string; end?: boolean }[] = [
  { to: '/',           label: 'Map',        end: true },
  { to: '/hotspots',   label: 'Hotspots' },
  { to: '/validation', label: 'Validation' },
  { to: '/method',     label: 'Method' },
]

function Nav() {
  return (
    <nav
      className="flex items-center gap-1 px-4 h-10 bg-chrome-900 border-b border-chrome-700 shrink-0 z-nav"
      aria-label="Primary navigation"
    >
      <span className="font-sans text-chrome-100 text-sm font-semibold mr-4 select-none">
        Surface AQI
      </span>
      {NAV_ITEMS.map(({ to, label, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            [
              'px-3 py-1 rounded text-sm font-sans transition-colors',
              isActive
                ? 'bg-chrome-700 text-chrome-100'
                : 'text-chrome-300 hover:text-chrome-100 hover:bg-chrome-700/50',
            ].join(' ')
          }
        >
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex flex-col h-screen overflow-hidden bg-chrome-900">
        <Nav />
        <main className="flex-1 relative overflow-hidden">
          <Routes>
            <Route path="/"           element={<MapPage />} />
            <Route path="/hotspots"   element={<HotspotsPage />} />
            <Route path="/validation" element={<ValidationPage />} />
            <Route path="/method"     element={<MethodPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
