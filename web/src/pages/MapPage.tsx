import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { MapView } from '../components/MapView'
import { Legend } from '../components/Legend'
import { Timeline } from '../components/Timeline'
import { LayerSwitcher } from '../components/LayerSwitcher'
import { PredictionDetailPanel } from '../components/PredictionDetailPanel'
import { StationModal } from '../components/StationModal'
import { PredictionResponse, LayerKey, StationFeature } from '../types/api'

export const MapPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()

  // URL View State defaults (SPEC.md §8) - centered over India
  const initialLat = parseFloat(searchParams.get('lat') || '22.0')
  const initialLon = parseFloat(searchParams.get('lon') || '82.0')
  const initialDate = searchParams.get('date') || '2026-09-15'
  const initialLayer = (searchParams.get('layer') as LayerKey) || 'aqi'

  const [lat, setLat] = useState<number>(initialLat)
  const [lon, setLon] = useState<number>(initialLon)
  const [zoom, setZoom] = useState<number>(4.2)
  const [date, setDate] = useState<string>(initialDate)
  const [layer, setLayer] = useState<LayerKey>(initialLayer)
  const [showGrid, setShowGrid] = useState<boolean>(true)

  // Prediction detail state
  const [predictLocation, setPredictLocation] = useState<{lat: number, lon: number} | null>(null)
  
  const predictMutation = useMutation<PredictionResponse, Error, { latitude: number, longitude: number, date: string }>({
    mutationFn: async (payload) => {
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        if (response.status === 422) {
          throw new Error('Environmental data is unavailable for this location/date. Please select another location or date.')
        }
        throw new Error('An unexpected error occurred while predicting AQI.')
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
    const base = new Date('2026-09-18')

    for (let i = 89; i >= 0; i--) {
      const d = new Date(base)
      d.setDate(d.getDate() - i)
      const dateStr = d.toISOString().slice(0, 10)
      dates.push(dateStr)

      // Roughly mark ~15% days as having satellite coverage gaps
      if (i % 7 === 0 || i % 11 === 0) {
        gaps.add(dateStr)
      }
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

    setPredictLocation({ lat: clickLat, lon: clickLon })
    predictMutation.mutate({ latitude: clickLat, longitude: clickLon, date })
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
          onMapClick={handleMapClick}
          onStationClick={(stn) => setSelectedStation(stn)}
          onMoveEnd={(newLat, newLon, newZoom) => {
            setLat(newLat)
            setLon(newLon)
            setZoom(newZoom)
          }}
        />

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
              isLoading={predictMutation.isPending}
              error={predictMutation.error ? predictMutation.error.message : null}
              onClose={() => {
                predictMutation.reset()
                setPredictLocation(null)
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
