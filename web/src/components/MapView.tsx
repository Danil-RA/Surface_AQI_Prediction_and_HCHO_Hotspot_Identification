import React, { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import { AQI_COLORS, StationFeature } from '../types/api'

interface MapViewProps {
  date: string
  layer: string
  lat: number
  lon: number
  zoom: number
  showGrid?: boolean
  selectedLocation?: { lat: number; lon: number } | null
  onMapClick?: (lat: number, lon: number) => void
  onStationClick?: (station: StationFeature) => void
  onMoveEnd?: (lat: number, lon: number, zoom: number) => void
}

export const MapView: React.FC<MapViewProps> = ({
  date,
  layer,
  lat,
  lon,
  zoom,
  showGrid = false,
  selectedLocation,
  onMapClick,
  onStationClick,
  onMoveEnd,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)

  // Use refs to avoid stale closure issues with event listeners
  const onMapClickRef = useRef(onMapClick)
  onMapClickRef.current = onMapClick

  const onStationClickRef = useRef(onStationClick)
  onStationClickRef.current = onStationClick

  const onMoveEndRef = useRef(onMoveEnd)
  onMoveEndRef.current = onMoveEnd

  // Initialize MapLibre
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return

    // Official Carto Dark Matter vector style (clean, no watermark, free for MapLibre)
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [lon, lat],
      zoom: zoom,
    })

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left')

    map.on('load', () => {
      // Add diagonal hatch pattern image for no-coverage cells
      const canvas = document.createElement('canvas')
      canvas.width = 16
      canvas.height = 16
      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.fillStyle = 'rgba(107, 114, 128, 0.35)'
        ctx.fillRect(0, 0, 16, 16)
        ctx.strokeStyle = 'rgba(107, 114, 128, 0.75)'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(-4, 12)
        ctx.lineTo(12, -4)
        ctx.moveTo(4, 20)
        ctx.lineTo(20, 4)
        ctx.stroke()
        const imgData = ctx.getImageData(0, 0, 16, 16)
        map.addImage('hatch-pattern', imgData)
      }

      // Add grid GeoJSON source
      map.addSource('aqi-grid', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })

      // Stepped fill layer for valid AQI values (hard edges at CPCB breakpoints)
      map.addLayer({
        id: 'aqi-grid-fill',
        type: 'fill',
        source: 'aqi-grid',
        filter: ['!=', ['get', 'coverage'], 'none'],
        layout: {
          visibility: showGrid ? 'visible' : 'none',
        },
        paint: {
          // Discrete stepped bands: Good (0-50), Satisfactory (51-100), Moderate (101-200),
          // Poor (201-300), Very Poor (301-400), Severe (401-500)
          'fill-color': [
            'step',
            ['get', 'value'],
            AQI_COLORS['Good'],
            51, AQI_COLORS['Satisfactory'],
            101, AQI_COLORS['Moderate'],
            201, AQI_COLORS['Poor'],
            301, AQI_COLORS['Very Poor'],
            401, AQI_COLORS['Severe']
          ],
          'fill-opacity': 0.75,
        },
      })

      // Dedicated hatch pattern layer for no-coverage cells (missing satellite data)
      map.addLayer({
        id: 'aqi-grid-no-coverage',
        type: 'fill',
        source: 'aqi-grid',
        filter: ['==', ['get', 'coverage'], 'none'],
        layout: {
          visibility: showGrid ? 'visible' : 'none',
        },
        paint: {
          'fill-pattern': 'hatch-pattern',
          'fill-opacity': 0.9,
        },
      })

      // Selected location point highlight
      map.addSource('selected-point', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })

      map.addLayer({
        id: 'selected-point-circle',
        type: 'circle',
        source: 'selected-point',
        paint: {
          'circle-radius': 7,
          'circle-color': '#F59E0B',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#FFFFFF',
        },
      })

      // Monitoring stations source & layers
      map.addSource('stations', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })

      // Station outer halo (distinct marker from grid cells)
      map.addLayer({
        id: 'stations-halo',
        type: 'circle',
        source: 'stations',
        paint: {
          'circle-radius': 8,
          'circle-color': '#0F172A',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#F1F5F9',
        },
      })

      // Station inner marker
      map.addLayer({
        id: 'stations-dot',
        type: 'circle',
        source: 'stations',
        paint: {
          'circle-radius': 4,
          'circle-color': '#38BDF8',
        },
      })

      setMapLoaded(true)
    })

    // Change cursor to crosshair/pointer over grid cells
    map.on('mouseenter', 'aqi-grid-fill', () => {
      map.getCanvas().style.cursor = 'pointer'
    })
    map.on('mouseleave', 'aqi-grid-fill', () => {
      map.getCanvas().style.cursor = ''
    })
    map.on('mouseenter', 'stations-halo', () => {
      map.getCanvas().style.cursor = 'pointer'
    })
    map.on('mouseleave', 'stations-halo', () => {
      map.getCanvas().style.cursor = ''
    })

    // Click handler
    map.on('click', (e) => {
      // Check if station was clicked
      const stationFeatures = map.queryRenderedFeatures(e.point, { layers: ['stations-halo', 'stations-dot'] })
      if (stationFeatures.length > 0 && onStationClickRef.current) {
        const props = stationFeatures[0].properties as any
        onStationClickRef.current({
          station_id: props.station_id,
          name: props.name,
          lat: props.lat,
          lon: props.lon,
          date: props.date,
          observed_aqi: props.observed_aqi ?? null,
          predicted_aqi: props.predicted_aqi ?? null,
          bias: props.bias ?? null,
        })
        return
      }

      if (onMapClickRef.current) {
        onMapClickRef.current(e.lngLat.lat, e.lngLat.lng)
      }
    })

    // Movement handler
    map.on('moveend', () => {
      if (onMoveEndRef.current) {
        const center = map.getCenter()
        onMoveEndRef.current(center.lat, center.lng, map.getZoom())
      }
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Fetch and update grid data whenever date or layer changes
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return

    const source = mapRef.current.getSource('aqi-grid') as maplibregl.GeoJSONSource
    if (!source) return

    fetch(`/api/grid?date=${date}&variable=${layer}&step=4`)
      .then((res) => res.json())
      .then((geojson) => {
        source.setData(geojson)
      })
      .catch((err) => console.error('Failed to load grid geojson:', err))
  }, [date, layer, mapLoaded])

  // Fetch and update station markers
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return

    const stationSource = mapRef.current.getSource('stations') as maplibregl.GeoJSONSource
    if (!stationSource) return

    fetch(`/api/stations?date=${date}`)
      .then((res) => res.json())
      .then((stations: StationFeature[]) => {
        const geojson = {
          type: 'FeatureCollection',
          features: stations.map((s) => ({
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [s.lon, s.lat],
            },
            properties: s,
          })),
        }
        stationSource.setData(geojson as any)
      })
      .catch((err) => console.error('Failed to load stations:', err))
  }, [date, mapLoaded])

  // Update selected location pin
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return

    const selectedSource = mapRef.current.getSource('selected-point') as maplibregl.GeoJSONSource
    if (!selectedSource) return

    if (selectedLocation) {
      selectedSource.setData({
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [selectedLocation.lon, selectedLocation.lat],
            },
            properties: {},
          },
        ],
      })
    } else {
      selectedSource.setData({ type: 'FeatureCollection', features: [] })
    }
  }, [selectedLocation, mapLoaded])

  // Toggle grid overlay visibility ON/OFF
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return

    const visibility = showGrid ? 'visible' : 'none'
    if (mapRef.current.getLayer('aqi-grid-fill')) {
      mapRef.current.setLayoutProperty('aqi-grid-fill', 'visibility', visibility)
    }
    if (mapRef.current.getLayer('aqi-grid-no-coverage')) {
      mapRef.current.setLayoutProperty('aqi-grid-no-coverage', 'visibility', visibility)
    }
  }, [showGrid, mapLoaded])

  return (
    <div className="w-full h-full relative">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  )
}
