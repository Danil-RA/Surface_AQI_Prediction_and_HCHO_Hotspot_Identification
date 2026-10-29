import React, { useState, useRef, useEffect } from 'react'

export interface SelectedLocationInfo {
  lat: number
  lon: number
  label?: string
}

interface LocationSearchProps {
  onSelectLocation: (loc: SelectedLocationInfo) => void
  onRequestPredict: (lat: number, lon: number) => void
  isPredicting?: boolean
  selectedLocation?: { lat: number; lon: number } | null
}

interface GeocodeResult {
  display_name: string
  lat: number
  lon: number
  type?: string
  class?: string
}

export const LocationSearch: React.FC<LocationSearchProps> = ({
  onSelectLocation,
  onRequestPredict,
  isPredicting = false,
  selectedLocation,
}) => {
  // Popup open/close state (hidden by default)
  const [isOpen, setIsOpen] = useState(false)
  const [searchMode, setSearchMode] = useState<'place' | 'coords'>('place')

  // Place search states
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<GeocodeResult[]>([])
  const [hasSearched, setHasSearched] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)

  // Coordinate search states
  const [latInput, setLatInput] = useState('')
  const [lonInput, setLonInput] = useState('')
  const [coordError, setCoordError] = useState<string | null>(null)

  // Active target location display
  const [activeTarget, setActiveTarget] = useState<SelectedLocationInfo | null>(null)

  const containerRef = useRef<HTMLDivElement>(null)
  const placeInputRef = useRef<HTMLInputElement>(null)

  // Sync external selectedLocation if it was clicked on the map
  useEffect(() => {
    if (selectedLocation) {
      if (
        !activeTarget ||
        Math.abs(activeTarget.lat - selectedLocation.lat) > 0.0001 ||
        Math.abs(activeTarget.lon - selectedLocation.lon) > 0.0001
      ) {
        setActiveTarget({
          lat: selectedLocation.lat,
          lon: selectedLocation.lon,
          label: `Coordinates (${selectedLocation.lat.toFixed(4)}°, ${selectedLocation.lon.toFixed(4)}°)`,
        })
      }
    }
  }, [selectedLocation])

  // Close popup and dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
        setShowDropdown(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick)
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [isOpen])

  // Close popup on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
        setShowDropdown(false)
      }
    }
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown)
    }
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  // Focus place input when popup opens in place mode
  useEffect(() => {
    if (isOpen && searchMode === 'place') {
      setTimeout(() => {
        placeInputRef.current?.focus()
      }, 50)
    }
  }, [isOpen, searchMode])

  // Execute Place Search
  const handlePlaceSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) return

    setIsSearching(true)
    setSearchError(null)
    setHasSearched(true)
    setShowDropdown(true)

    try {
      // Primary: backend proxy
      let res = await fetch(`/api/geocode?q=${encodeURIComponent(trimmed)}&limit=5`)
      let data: GeocodeResult[] = []

      if (res.ok) {
        data = await res.json()
      } else {
        // Fallback: direct Nominatim call
        const fallbackRes = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(trimmed)}&limit=5&addressdetails=1`
        )
        if (fallbackRes.ok) {
          const raw = await fallbackRes.json()
          data = raw.map((item: any) => ({
            display_name: item.display_name,
            lat: parseFloat(item.lat),
            lon: parseFloat(item.lon),
            type: item.type,
            class: item.class,
          }))
        }
      }

      setSearchResults(data)
    } catch (err) {
      setSearchError('Search failed. Please check your network connection.')
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  // Handle Selection of a Place Result
  const handleSelectResult = (result: GeocodeResult) => {
    const loc: SelectedLocationInfo = {
      lat: result.lat,
      lon: result.lon,
      label: result.display_name,
    }
    setActiveTarget(loc)
    setShowDropdown(false)
    onSelectLocation(loc)
  }

  // Execute Coordinate Search
  const handleCoordinateSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setCoordError(null)

    const latVal = parseFloat(latInput.trim())
    const lonVal = parseFloat(lonInput.trim())

    if (isNaN(latVal) || isNaN(lonVal)) {
      setCoordError('Please enter valid numeric latitude and longitude values.')
      return
    }

    if (latVal < -90 || latVal > 90) {
      setCoordError('Latitude must be between -90.0° and 90.0°.')
      return
    }

    if (lonVal < -180 || lonVal > 180) {
      setCoordError('Longitude must be between -180.0° and 180.0°.')
      return
    }

    const loc: SelectedLocationInfo = {
      lat: latVal,
      lon: lonVal,
      label: `Coordinates (${latVal.toFixed(4)}°, ${lonVal.toFixed(4)}°)`,
    }

    setActiveTarget(loc)
    onSelectLocation(loc)
  }

  // Trigger Prediction
  const handlePredictClick = () => {
    if (!activeTarget) return
    onRequestPredict(activeTarget.lat, activeTarget.lon)
  }

  return (
    <div ref={containerRef} className="relative pointer-events-auto font-sans text-xs">
      {/* 1. Compact Trigger Button (visible by default) */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className={[
          'px-3 py-1.5 rounded shadow-lg backdrop-blur border text-xs font-medium flex items-center gap-1.5 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500/50',
          isOpen
            ? 'bg-chrome-800 text-sky-400 border-sky-500/70 shadow-sky-950/40'
            : 'bg-chrome-900/90 text-chrome-100 border-chrome-700 hover:bg-chrome-800 hover:text-white',
        ].join(' ')}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        title="Find location by name or coordinates"
      >
        <svg
          className="w-3.5 h-3.5 text-sky-400 shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <span>Find Location</span>
      </button>

      {/* 2. Floating Popup Panel (rendered only when open) */}
      {isOpen && (
        <div
          className="absolute top-full left-0 mt-2 w-80 sm:w-96 max-w-[calc(100vw-2rem)] bg-chrome-900/95 backdrop-blur-md border border-chrome-700 rounded shadow-2xl z-50"
          role="dialog"
          aria-label="Location search dialog"
        >
          {/* Header: Mode Switcher & Close button */}
          <div className="p-2 border-b border-chrome-700/80 flex items-center justify-between gap-2 bg-chrome-900 rounded-t">
            <div className="flex bg-chrome-800/80 p-0.5 rounded border border-chrome-700/60">
              <button
                type="button"
                onClick={() => {
                  setSearchMode('place')
                  setCoordError(null)
                }}
                className={[
                  'px-2.5 py-1 rounded text-2xs font-medium transition-colors',
                  searchMode === 'place'
                    ? 'bg-sky-500/20 text-sky-400 font-semibold shadow-xs'
                    : 'text-chrome-400 hover:text-chrome-200',
                ].join(' ')}
              >
                Place Name
              </button>
              <button
                type="button"
                onClick={() => {
                  setSearchMode('coords')
                  setShowDropdown(false)
                }}
                className={[
                  'px-2.5 py-1 rounded text-2xs font-medium transition-colors',
                  searchMode === 'coords'
                    ? 'bg-sky-500/20 text-sky-400 font-semibold shadow-xs'
                    : 'text-chrome-400 hover:text-chrome-200',
                ].join(' ')}
              >
                Coordinates
              </button>
            </div>

            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="text-chrome-400 hover:text-chrome-100 hover:bg-chrome-800 p-1 rounded transition-colors text-xs flex items-center justify-center w-6 h-6"
              title="Close search popup (Esc)"
              aria-label="Close search popup"
            >
              ✕
            </button>
          </div>

          {/* Mode A: Place Name Search */}
          {searchMode === 'place' && (
            <div className="p-3 space-y-2 relative z-30">
              <form onSubmit={handlePlaceSearch} className="flex gap-1.5 relative">
                <div className="relative flex-1">
                  <input
                    ref={placeInputRef}
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => {
                      if (searchResults.length > 0) setShowDropdown(true)
                    }}
                    placeholder="Search city, town, locality..."
                    className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-900 placeholder-slate-500 caret-slate-900 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 pr-7 transition-colors shadow-xs"
                    aria-label="Search location by place name"
                  />
                  {query && (
                    <button
                      type="button"
                      onClick={() => {
                        setQuery('')
                        setSearchResults([])
                        setHasSearched(false)
                        setShowDropdown(false)
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs p-0.5"
                      title="Clear search input"
                    >
                      ✕
                    </button>
                  )}

                  {/* Results Dropdown attached immediately below the search input */}
                  {showDropdown && (
                    <div
                      onMouseDown={(e) => e.stopPropagation()}
                      className="absolute top-full left-0 right-0 mt-1 z-50 bg-chrome-900 border border-chrome-700 rounded shadow-2xl max-h-56 overflow-y-auto custom-scrollbar"
                    >
                      {isSearching ? (
                        <div className="p-3 text-center text-chrome-400 text-xs animate-pulse">
                          Searching matching locations...
                        </div>
                      ) : searchError ? (
                        <div className="p-3 text-rose-400 text-xs text-center">
                          {searchError}
                        </div>
                      ) : searchResults.length === 0 && hasSearched ? (
                        <div className="p-3 text-chrome-400 text-xs text-center">
                          No locations found for &ldquo;{query}&rdquo;. Try another search term or enter coordinates.
                        </div>
                      ) : (
                        searchResults.map((result, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => handleSelectResult(result)}
                            className="w-full text-left p-2.5 hover:bg-chrome-800 border-b border-chrome-800/60 last:border-0 transition-colors flex flex-col gap-0.5 group"
                            title={result.display_name}
                          >
                            <span className="text-chrome-100 font-medium text-xs group-hover:text-sky-300 transition-colors line-clamp-1">
                              {result.display_name}
                            </span>
                            <span className="text-3xs text-chrome-400 font-mono">
                              {result.lat.toFixed(4)}°, {result.lon.toFixed(4)}°
                            </span>
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isSearching || !query.trim()}
                  className="bg-sky-600 hover:bg-sky-500 disabled:bg-chrome-800 disabled:text-chrome-500 text-white font-medium px-3 py-1.5 rounded text-xs transition-colors shrink-0 flex items-center gap-1 shadow-xs"
                >
                  {isSearching ? (
                    <span className="animate-spin text-2xs">↻</span>
                  ) : (
                    <span>Search</span>
                  )}
                </button>
              </form>
            </div>
          )}

          {/* Mode B: Coordinate Search */}
          {searchMode === 'coords' && (
            <form onSubmit={handleCoordinateSearch} className="p-3 space-y-2.5">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-3xs font-medium text-chrome-300 mb-1">
                    Latitude (-90 to 90)
                  </label>
                  <input
                    type="text"
                    value={latInput}
                    onChange={(e) => setLatInput(e.target.value)}
                    placeholder="e.g. 28.6139"
                    className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-900 placeholder-slate-500 caret-slate-900 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 tabular transition-colors shadow-xs"
                    aria-label="Latitude input"
                  />
                </div>
                <div>
                  <label className="block text-3xs font-medium text-chrome-300 mb-1">
                    Longitude (-180 to 180)
                  </label>
                  <input
                    type="text"
                    value={lonInput}
                    onChange={(e) => setLonInput(e.target.value)}
                    placeholder="e.g. 77.2090"
                    className="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-900 placeholder-slate-500 caret-slate-900 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 tabular transition-colors shadow-xs"
                    aria-label="Longitude input"
                  />
                </div>
              </div>

              {coordError && (
                <div className="text-rose-400 text-2xs font-medium bg-rose-950/40 border border-rose-800/50 rounded p-1.5">
                  {coordError}
                </div>
              )}

              <div className="flex justify-end">
                <button
                  type="submit"
                  className="bg-sky-600 hover:bg-sky-500 text-white font-medium px-3 py-1.5 rounded text-xs transition-colors shadow-xs"
                >
                  Search Location
                </button>
              </div>
            </form>
          )}

          {/* Selected Target Action Card */}
          {activeTarget && (
            <div className="p-3 border-t border-chrome-700/80 bg-chrome-800/40 flex flex-col gap-2.5">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="text-3xs text-amber-400 font-semibold uppercase tracking-wider flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                    Target Location Selected
                  </div>
                  <div
                    className="text-xs font-medium text-chrome-100 truncate mt-0.5"
                    title={activeTarget.label}
                  >
                    {activeTarget.label || 'Selected Target'}
                  </div>
                  <div className="text-3xs text-chrome-400 font-mono mt-0.5">
                    {activeTarget.lat.toFixed(4)}° N, {activeTarget.lon.toFixed(4)}° E
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setActiveTarget(null)}
                  className="text-chrome-400 hover:text-chrome-200 text-xs p-1"
                  title="Deselect location"
                >
                  ✕
                </button>
              </div>

              {/* Clean Professional Predict Button (no emojis) */}
              <button
                type="button"
                onClick={handlePredictClick}
                disabled={isPredicting}
                className="w-full bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 disabled:bg-chrome-700 disabled:text-chrome-400 disabled:cursor-not-allowed text-white font-medium py-2 px-3 rounded text-xs transition-colors flex items-center justify-center gap-1.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-1 focus:ring-offset-chrome-900"
              >
                {isPredicting ? (
                  <>
                    <span className="animate-spin text-2xs">↻</span>
                    <span>Predicting AQI...</span>
                  </>
                ) : (
                  <span>Predict Surface AQI</span>
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
