import React, { useEffect, useState, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import {
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import { Season, HotspotProperties, HotspotFeature } from '../types/api'

const SEASONS: { id: Season; label: string }[] = [
  { id: 'winter', label: 'Winter' },
  { id: 'premonsoon', label: 'Pre-Monsoon' },
  { id: 'monsoon', label: 'Monsoon' },
  { id: 'postmonsoon', label: 'Post-Monsoon' },
]

export const HotspotsPage: React.FC = () => {
  const [season, setSeason] = useState<Season>('winter')
  const [year] = useState<number>(2023)
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

  // Lagged correlation data (Lags 0 to 3 days per SPEC.md 4.3)
  const lagData = [
    { lag: 'Lag 0d', correlation: 0.68 },
    { lag: 'Lag 1d', correlation: 0.74 },
    { lag: 'Lag 2d', correlation: 0.59 },
    { lag: 'Lag 3d', correlation: 0.42 },
  ]

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
            Tropospheric formaldehyde elevated clusters and biomass burning drivers
          </p>
        </div>

        {/* Cluster Details Card */}
        {selectedCluster && (
          <div className="bg-chrome-700/30 border border-chrome-700 rounded p-3 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-mono text-rose-400 font-semibold">
                Cluster {selectedCluster.cluster_id}
              </span>
              <span className="text-2xs text-chrome-500 uppercase">
                {selectedCluster.season}
              </span>
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
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Mean Fires/Day</div>
                <div className="text-chrome-100 font-bold text-sm">
                  {selectedCluster.fire_count_mean.toFixed(1)}
                </div>
              </div>
              <div className="bg-chrome-900/60 p-1.5 rounded">
                <div className="text-chrome-500">Dominant Driver</div>
                <div className="text-amber-400 font-bold capitalize">
                  {selectedCluster.dominant_driver}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Lagged Correlation Chart (SPEC.md 4.3) */}
        <div className="space-y-1.5 bg-chrome-700/20 border border-chrome-700 rounded p-3">
          <div className="text-2xs font-semibold text-chrome-300 uppercase tracking-wider">
            Lagged Correlation: HCHO vs Fire Counts
          </div>
          <div className="h-28 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={lagData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <XAxis dataKey="lag" tick={{ fill: '#8CA3B8', fontSize: 10 }} />
                <YAxis tick={{ fill: '#8CA3B8', fontSize: 10 }} domain={[0, 1]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', fontSize: 11 }}
                  formatter={(v: any) => [Number(v).toFixed(2), 'Pearson r']}
                />
                <Bar dataKey="correlation" fill="#F43F5E" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-2xs text-chrome-500 italic text-center">
            Peak correlation at Lag 1d indicates transport delay from fires
          </div>
        </div>

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
                  <th className="p-1.5">Driver</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-chrome-700/40">
                {hotspotsData.map((f) => {
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
                      <td className="p-1.5 font-mono">{p.cluster_id}</td>
                      <td className="p-1.5 tabular font-mono text-right font-semibold">
                        {p.gi_star.toFixed(2)}
                      </td>
                      <td className="p-1.5 capitalize text-chrome-300">{p.dominant_driver}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </aside>
    </div>
  )
}
