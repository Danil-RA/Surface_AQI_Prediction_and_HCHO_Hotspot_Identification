import React, { useEffect, useState, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import { Season, HotspotProperties, HotspotFeature } from '../types/api'

const SEASONS: { id: Season; label: string }[] = [
  { id: 'winter', label: 'Winter' },
  { id: 'premonsoon', label: 'Pre-Monsoon' },
  { id: 'monsoon', label: 'Monsoon' },
  { id: 'postmonsoon', label: 'Post-Monsoon' },
]

export const HotspotsPage: React.FC = () => {
  const [season, setSeason] = useState<Season>('winter')
  const [year] = useState<number>(2024)
  const [hotspotsData, setHotspotsData] = useState<HotspotFeature[]>([])
  const [selectedCluster, setSelectedCluster] = useState<HotspotProperties | null>(null)

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)

  // Initialize Map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [78.0, 20.0],
      zoom: 4.5,
    })

    map.on('load', () => {
      map.addSource('hotspots-src', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })

      // Hotspot polygons with opacity keyed to Getis-Ord Gi* significance (SPEC.md 4.3)
      map.addLayer({
        id: 'hotspot-polygons',
        type: 'fill',
        source: 'hotspots-src',
        paint: {
          'fill-color': '#F43F5E',
          // Opacity keyed to gi_star (range roughly 1.5 to 8.0)
          'fill-opacity': [
            'interpolate',
            ['linear'],
            ['get', 'gi_star'],
            1.5, 0.25,
            4.0, 0.55,
            8.0, 0.85,
          ],
        },
      })

      map.addLayer({
        id: 'hotspot-lines',
        type: 'line',
        source: 'hotspots-src',
        paint: {
          'line-color': '#FDA4AF',
          'line-width': 1.5,
        },
      })

      map.on('click', 'hotspot-polygons', (e) => {
        if (e.features && e.features[0]) {
          setSelectedCluster(e.features[0].properties as any)
        }
      })

      setMapLoaded(true)
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Fetch hotspots when season changes
  useEffect(() => {
    fetch(`/api/hotspots?season=${season}&year=${year}`)
      .then((res) => res.json())
      .then((data: any) => {
        const features: HotspotFeature[] = data.features || []
        setHotspotsData(features)
        if (features.length > 0) {
          setSelectedCluster(features[0].properties)
        }

        if (mapRef.current && mapLoaded) {
          const src = mapRef.current.getSource('hotspots-src') as maplibregl.GeoJSONSource
          if (src) src.setData(data)
        }
      })
      .catch((err) => {
        console.error('Failed to load hotspots:', err)
      })
  }, [season, year, mapLoaded])

  return (
    <div className="flex h-full w-full overflow-hidden font-sans">
      {/* Map View */}
      <div className="flex-1 relative h-full">
        <div ref={mapContainer} className="w-full h-full" />

        {/* Season Selector Overlay */}
        <div className="absolute top-4 left-4 z-panel bg-chrome-900/90 backdrop-blur border border-chrome-700 rounded p-2 flex gap-1 shadow-lg">
          {SEASONS.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setSeason(id)}
              className={[
                'px-3 py-1 rounded text-xs transition-colors',
                season === id
                  ? 'bg-rose-500 text-white font-semibold'
                  : 'text-chrome-300 hover:text-chrome-100 hover:bg-chrome-700/50',
              ].join(' ')}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Side Panel: Ranked Cluster Table & Lagged Fire Correlation */}
      <aside className="w-96 bg-chrome-900 border-l border-chrome-700 p-4 flex flex-col gap-4 overflow-y-auto shrink-0">
        <div>
          <h1 className="text-base font-semibold text-chrome-100">
            HCHO Hotspots Analysis
          </h1>
          <p className="text-2xs text-chrome-300 mt-0.5">
            Tropospheric formaldehyde elevated clusters and fire association analysis
          </p>
        </div>

        {/* Cluster Details Card */}
        {selectedCluster ? (
          <div className="bg-chrome-700/30 border border-chrome-700 rounded p-3 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-mono text-rose-400 font-semibold">
                Cluster {selectedCluster.cluster_id.substring(0, 8)}
              </span>
              <span className="text-2xs text-chrome-500 uppercase">
                {selectedCluster.season} {selectedCluster.year}
              </span>
            </div>
            
            <div className="text-2xs text-chrome-400 font-medium pt-1 pb-0.5 border-b border-chrome-700/50">
              Statistical Significance
            </div>
            <div className="grid grid-cols-2 gap-2 text-2xs tabular font-mono">
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Gi* Statistic</div>
                <div className="text-chrome-100 font-bold text-sm">
                  {selectedCluster.gi_star.toFixed(2)}
                </div>
              </div>
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Mean HCHO</div>
                <div className="text-chrome-100 font-bold text-sm">
                  {selectedCluster.mean_hcho.toExponential(2)}
                </div>
              </div>
            </div>

            <div className="text-2xs text-chrome-400 font-medium pt-2 pb-0.5 border-b border-chrome-700/50">
              Fire Association
            </div>
            <div className="grid grid-cols-2 gap-2 text-2xs tabular font-mono">
              <div className="bg-chrome-900/60 p-1.5 rounded col-span-2">
                <div className="text-chrome-500">Driver</div>
                <div className="text-amber-400 font-bold capitalize text-sm">
                  {selectedCluster.dominant_driver.replace(/_/g, ' ')}
                </div>
              </div>
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Total Fires</div>
                <div className="text-chrome-100 font-bold">
                  {Math.round(selectedCluster.fire_count_total)}
                </div>
              </div>
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Active Days</div>
                <div className="text-chrome-100 font-bold">
                  {selectedCluster.fire_active_days}
                </div>
              </div>
            </div>

            <div className="text-2xs text-chrome-400 font-medium pt-2 pb-0.5 border-b border-chrome-700/50">
              Meteorology
            </div>
            <div className="grid grid-cols-2 gap-2 text-2xs tabular font-mono">
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Mean Temp</div>
                <div className="text-chrome-100">{selectedCluster.mean_temperature.toFixed(1)} °C</div>
              </div>
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Mean RH</div>
                <div className="text-chrome-100">{selectedCluster.mean_relative_humidity.toFixed(1)} %</div>
              </div>
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Wind Speed</div>
                <div className="text-chrome-100">{selectedCluster.mean_wind_speed.toFixed(1)} m/s</div>
              </div>
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Precipitation</div>
                <div className="text-chrome-100">{(selectedCluster.mean_precipitation * 1000).toFixed(2)} mm</div>
              </div>
            </div>
            
            <div className="text-2xs text-chrome-500 text-right pt-2">
              Area: {Math.round(selectedCluster.area_km2).toLocaleString()} km²
            </div>
          </div>
        ) : (
          <div className="text-2xs text-chrome-500 italic p-4 text-center border border-dashed border-chrome-700 rounded">
            {hotspotsData.length > 0 ? 'Select a cluster on the map' : 'Data unavailable for this season.'}
          </div>
        )}

        {/* Ranked Cluster Table */}
        <div className="space-y-1.5 flex-1 flex flex-col">
          <div className="text-2xs font-semibold text-chrome-300 uppercase tracking-wider">
            Ranked Spatial Clusters
          </div>
          <div className="border border-chrome-700 rounded overflow-hidden flex-1 overflow-y-auto">
            <table className="w-full text-left text-2xs border-collapse">
              <thead className="bg-chrome-700/50 text-chrome-300 font-semibold sticky top-0">
                <tr>
                  <th className="p-1.5">ID</th>
                  <th className="p-1.5 tabular text-right">Gi*</th>
                  <th className="p-1.5 tabular text-right">Fires</th>
                  <th className="p-1.5">Association</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-chrome-700/40">
                {hotspotsData.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-chrome-500 italic">No clusters found</td>
                  </tr>
                ) : (
                  hotspotsData
                    .sort((a, b) => b.properties.gi_star - a.properties.gi_star)
                    .map((f) => {
                    const p = f.properties
                    const isSelected = selectedCluster?.cluster_id === p.cluster_id
                    return (
                      <tr
                        key={p.cluster_id}
                        onClick={() => setSelectedCluster(p)}
                        className={[
                          'cursor-pointer transition-colors',
                          isSelected ? 'bg-rose-950/40 text-rose-200' : 'hover:bg-chrome-700/30 text-chrome-100',
                        ].join(' ')}
                      >
                        <td className="p-1.5 font-mono" title={p.cluster_id}>{p.cluster_id.substring(0, 5)}</td>
                        <td className="p-1.5 tabular font-mono text-right font-semibold">
                          {p.gi_star.toFixed(2)}
                        </td>
                        <td className="p-1.5 tabular font-mono text-right text-chrome-400">
                          {Math.round(p.fire_count_total)}
                        </td>
                        <td className="p-1.5 capitalize text-chrome-300">
                          {p.dominant_driver.replace(/_/g, ' ')}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </aside>
    </div>
  )
}
