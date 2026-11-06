import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { MapView } from '../components/MapView'
import { Legend } from '../components/Legend'
import { Timeline } from '../components/Timeline'
import { LayerSwitcher } from '../components/LayerSwitcher'
import { PredictionDetailPanel } from '../components/PredictionDetailPanel'
import { StationModal } from '../components/StationModal'
import { LocationSearch, SelectedLocationInfo } from '../components/LocationSearch'
import { PredictionResponse, LayerKey, StationFeature } from '../types/api'

export const MapPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()

  // URL View State defaults (SPEC.md §8) - centered over India
  const initialLat = parseFloat(searchParams.get('lat') || '22.0')
  const initialLon = parseFloat(searchParams.get('lon') || '82.0')
  const initialDate = searchParams.get('date') || new Date(Date.now() - 86400000).toISOString().slice(0, 10)
  const initialLayer = (searchParams.get('layer') as LayerKey) || 'aqi'

  const [lat, setLat] = useState<number>(initialLat)
  const [lon, setLon] = useState<number>(initialLon)
  const [zoom, setZoom] = useState<number>(4.2)
  const [date, setDate] = useState<string>(initialDate)
  const [layer, setLayer] = useState<LayerKey>(initialLayer)
  const [showGrid, setShowGrid] = useState<boolean>(false)

  // Prediction detail state
  const [predictLocation, setPredictLocation] = useState<{lat: number, lon: number} | null>(null)
  const [focusTrigger, setFocusTrigger] = useState<{lat: number, lon: number, zoom?: number} | null>(null)
  const [selectedSearchLabel, setSelectedSearchLabel] = useState<string | null>(null)
  
  const predictMutation = useMutation<
    PredictionResponse,
    Error,
    { latitude: number; longitude: number; date: string; locationName?: string }
  >({
    mutationFn: async (payload) => {
      let response: Response;
      try {
        response = await fetch('/api/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            latitude: payload.latitude,
            longitude: payload.longitude,
            date: payload.date,
          })
        })
      } catch (err) {
        throw new Error('Network error: Unable to reach the prediction server.')
      }
      
      let data;
      try {
        data = await response.json()
      } catch (err) {
        throw new Error('Failed to parse response from server. An unexpected error occurred.')
      }
      
      if (!response.ok) {
        if (response.status === 422) {
          // Check if it is actually the custom environmental data missing error
          // FastAPI validation errors (e.g. out of bounds longitude) return a list for detail
          if (data && typeof data.detail === 'object' && data.detail !== null && data.detail.message === 'Environmental data is unavailable for this location/date.') {
            throw new Error(JSON.stringify({ type: 'MISSING_DATA', ...data.detail }))
          }
          // Legacy check just in case
          if (data && typeof data.detail === 'string' && data.detail.includes('Environmental data unavailable')) {
            throw new Error('Environmental data is unavailable for this location/date. Please select another location or date.')
          }
          // Otherwise, it's a validation error
          const msg = data && data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : 'Invalid request data provided.';
          throw new Error(`Validation Error: ${msg}`)
        }
        
        // Handle 500 and other errors
        const msg = data && typeof data.detail === 'string' ? data.detail : 'An unexpected error occurred while predicting AQI.'
        throw new Error(msg)
      }
      
      return data
    }
  })

  // Station modal state
  const [selectedStation, setSelectedStation] = useState<StationFeature | null>(null)

  // Available timeline dates (90 days ending today)
  const [timelineDates, setTimelineDates] = useState<string[]>([])
  const [gapDates, setGapDates] = useState<Set<string>>(new Set())

  // Generate date range
  useEffect(() => {
    const dates: string[] = []
    const gaps = new Set<string>()
    const base = new Date()

    for (let i = 89; i >= 0; i--) {
      const d = new Date(base)
      d.setDate(d.getDate() - i)
      const dateStr = d.toISOString().slice(0, 10)
      dates.push(dateStr)
    }

    setTimelineDates(dates)
    setGapDates(gaps)
  }, [])

  // Update URL search parameters when state changes (enables link shareability)
  useEffect(() => {
    const nextParams = new URLSearchParams()
    nextParams.set('lat', lat.toFixed(2))
    nextParams.set('lon', lon.toFixed(2))
    nextParams.set('date', date)
    nextParams.set('layer', layer)
    setSearchParams(nextParams, { replace: true })
  }, [lat, lon, date, layer, setSearchParams])

  // Handle click on map anywhere -> POST /api/predict
  const handleMapClick = (clickLat: number, clickLon: number) => {
    // If a request is already running, avoid duplicating it
    if (predictMutation.isPending) return;

    setSelectedSearchLabel(null)
    setPredictLocation({ lat: clickLat, lon: clickLon })
    predictMutation.mutate({ latitude: clickLat, longitude: clickLon, date, locationName: undefined })
  }

  // Handle location selection from search (place name or coordinates)
  const handleSelectSearchLocation = (loc: SelectedLocationInfo) => {
    setSelectedSearchLabel(loc.label || null)
    setPredictLocation({ lat: loc.lat, lon: loc.lon })
    setFocusTrigger({ lat: loc.lat, lon: loc.lon, zoom: 10 })
  }

  // Handle explicit predict request from search
  const handleRequestPredict = (targetLat: number, targetLon: number, label?: string) => {
    if (predictMutation.isPending) return
    const resolvedLabel = label || selectedSearchLabel || undefined
    setSelectedSearchLabel(resolvedLabel || null)
    setPredictLocation({ lat: targetLat, lon: targetLon })
    setFocusTrigger({ lat: targetLat, lon: targetLon, zoom: 10 })
    predictMutation.mutate({ latitude: targetLat, longitude: targetLon, date, locationName: resolvedLabel })
  }

  return (
    <div className="relative w-full h-full overflow-hidden flex flex-col">
      {/* Full-bleed Map Canvas */}
      <div className="flex-1 relative">
        <MapView
          date={date}
          layer={layer}
          lat={lat}
          lon={lon}
          zoom={zoom}
          showGrid={showGrid}
          selectedLocation={predictLocation}
          focusTrigger={focusTrigger}
          onMapClick={handleMapClick}
          onStationClick={(stn) => setSelectedStation(stn)}
          onMoveEnd={(newLat, newLon, newZoom) => {
            setLat(newLat)
            setLon(newLon)
            setZoom(newZoom)
          }}
        />

        {/* Location Search Bar & Selector (Top-Left) */}
        <div className="absolute top-4 left-14 z-panel">
          <LocationSearch
            onSelectLocation={handleSelectSearchLocation}
            onRequestPredict={handleRequestPredict}
            isPredicting={predictMutation.isPending}
            selectedLocation={predictLocation}
          />
        </div>

        {/* Permanent Legend (Bottom-Left) */}
        <div className="absolute bottom-4 left-4 z-legend">
          <Legend />
        </div>

        {/* Layer Switcher (Top-Right) */}
        <div className="absolute top-4 right-4 z-panel">
          <LayerSwitcher
            selectedLayer={layer}
            onLayerSelect={setLayer}
            showGrid={showGrid}
            onToggleGrid={setShowGrid}
          />
        </div>

        {/* Prediction Detail Drawer */}
        {(predictMutation.data || predictMutation.isPending || predictMutation.isError) ? (
          <div className="absolute top-4 right-48 z-panel">
            <PredictionDetailPanel
              data={predictMutation.data || null}
              locationName={predictMutation.variables?.locationName || null}
              isLoading={predictMutation.isPending}
              error={predictMutation.error ? predictMutation.error.message : null}
              onClose={() => {
                predictMutation.reset()
                setPredictLocation(null)
                setSelectedSearchLabel(null)
              }}
            />
          </div>
        ) : null}

        {/* Station Measured vs Estimated Popup Modal */}
        <StationModal
          station={selectedStation}
          onClose={() => setSelectedStation(null)}
        />
      </div>

      {/* Scrubbable Date Timeline (Bottom Track) */}
      <Timeline
        dates={timelineDates}
        selectedDate={date}
        onDateSelect={setDate}
        noCoverageDates={gapDates}
      />
    </div>
  )
}
