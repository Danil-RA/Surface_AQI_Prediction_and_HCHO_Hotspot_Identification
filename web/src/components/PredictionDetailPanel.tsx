import React from 'react'
import { PredictionResponse, AQI_COLORS } from '../types/api'

interface PredictionDetailPanelProps {
  data: PredictionResponse | null
  isLoading: boolean
  error: string | null
  onClose: () => void
}

export const PredictionDetailPanel: React.FC<PredictionDetailPanelProps> = ({
  data,
  isLoading,
  error,
  onClose,
}) => {
  if (!data && !isLoading && !error) return null

  return (
    <div
      className="relative w-80 max-w-[calc(100vw-2rem)] bg-chrome-900/95 backdrop-blur-md border border-chrome-700 rounded shadow-2xl flex flex-col max-h-[calc(100vh-8.5rem)] overflow-hidden transition-all duration-300 font-sans"
      role="dialog"
      aria-labelledby="prediction-detail-heading"
      onWheel={(e) => e.stopPropagation()}
      onTouchMove={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-chrome-700/80 bg-chrome-900 shrink-0">
        <div>
          <h2 id="prediction-detail-heading" className="text-sm font-semibold text-chrome-100">
            Real-time Prediction
          </h2>
          {data && (
            <div className="tabular text-chrome-300 text-2xs font-mono">
              {data.location.latitude.toFixed(3)}°N, {data.location.longitude.toFixed(3)}°E • {data.date}
            </div>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-chrome-500 hover:text-chrome-100 p-1 rounded hover:bg-chrome-700"
          aria-label="Close panel"
        >
          ✕
        </button>
      </div>

      <div className="p-4 space-y-4 overflow-y-auto overscroll-contain flex-1 custom-scrollbar">
        {isLoading ? (
          <div className="text-chrome-300 text-xs py-8 text-center animate-pulse">
            Loading prediction...
          </div>
        ) : error ? (
          (() => {
            try {
              const errObj = JSON.parse(error)
              if (errObj.type === 'MISSING_DATA') {
                const filterVWS = (list: any[]) =>
                  (list || [])
                    .filter((src: any) => src.source !== 'Synthetic VWS')
                    .map((src: any) => ({
                      ...src,
                      variables: (src.variables || []).filter((v: string) => v !== 'VWS'),
                    }))
                    .filter((src: any) => src.variables.length > 0)

                const missingData = filterVWS(errObj.missing_data)
                const availableData = filterVWS(errObj.available_data)

                return (
                  <div className="bg-chrome-700/30 border border-chrome-700 rounded p-4 text-left space-y-4">
                    <div className="text-sm font-semibold text-amber-400 text-center border-b border-chrome-700/50 pb-2">
                      Environmental Data Status
                    </div>
                    <p className="text-xs text-chrome-300 text-center">
                      Environmental data is unavailable for this location/date.
                    </p>
                    
                    {missingData.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-rose-400 mb-2">
                          ✕ Missing data
                        </div>
                        <div className="space-y-2 text-xs pl-1">
                          {missingData.map((src: any) => (
                            <div key={src.source}>
                              <div className="font-medium text-chrome-100">{src.source}</div>
                              <ul className="list-none pl-3 text-chrome-300 mt-0.5 space-y-0.5">
                                {src.variables.map((v: string) => (
                                  <li key={v} className="flex items-center gap-1.5 before:content-['•'] before:text-chrome-500">
                                    {v.replace('NO2', 'NO₂').replace('SO2', 'SO₂').replace('O3', 'O₃')}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {availableData.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-emerald-400 mb-2 border-t border-chrome-700/50 pt-3">
                          ✓ Available data
                        </div>
                        <div className="space-y-2 text-xs pl-1">
                          {availableData.map((src: any) => (
                            <div key={src.source}>
                              <div className="font-medium text-chrome-100">{src.source}</div>
                              <ul className="list-none pl-3 text-chrome-300 mt-0.5 space-y-0.5">
                                {src.variables.map((v: string) => (
                                  <li key={v} className="flex items-center gap-1.5 before:content-['•'] before:text-chrome-500">
                                    {v.replace('NO2', 'NO₂').replace('SO2', 'SO₂').replace('O3', 'O₃')}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              }
            } catch (e) {
              // Not JSON or unknown format, fallback to standard text error
            }
            return (
              <div className="bg-chrome-700/30 border border-chrome-700 rounded p-4 text-center space-y-2">
                <div className="text-sm font-semibold text-amber-400">
                  Prediction Failed
                </div>
                <p className="text-xs text-chrome-300 leading-relaxed">{error}</p>
              </div>
            )
          })()
        ) : data ? (
          <>
            {/* Primary AQI Readout */}
            <div className="flex items-center justify-between bg-chrome-700/30 border border-chrome-700 rounded p-3">
              <div>
                <div className="text-3xl font-bold text-chrome-100 tabular font-mono">
                  {data.aqi.value}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: AQI_COLORS[data.aqi.category] || '#6B7280' }}
                  />
                  <span className="text-xs font-semibold text-chrome-100">
                    {data.aqi.category}
                  </span>
                </div>
              </div>

              <div className="text-right">
                <div className="text-2xs text-chrome-500 uppercase tracking-wider">
                  Dominant Pollutant
                </div>
                <div className="text-sm font-semibold text-amber-400 font-mono mt-0.5">
                  {data.dominant_pollutant}
                </div>
              </div>
            </div>

            {/* Pollutant Predictions Grid */}
            <div className="space-y-2">
              <div className="text-2xs font-semibold text-chrome-300 uppercase tracking-wider">
                Predicted Concentrations
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(data.predictions).map(([p, value]) => (
                  <div key={p} className="bg-chrome-700/40 p-2 rounded border border-chrome-700/60 flex justify-between items-center">
                    <div className="text-2xs text-chrome-300 font-medium">{p}</div>
                    <div className="tabular font-mono font-semibold text-chrome-100">
                      {value.toFixed(1)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Sub-indices Grid */}
            <div className="space-y-2">
              <div className="text-2xs font-semibold text-chrome-300 uppercase tracking-wider">
                Sub-indices
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                {Object.entries(data.sub_indices).map(([p, value]) => (
                  <div key={p} className="bg-chrome-700/40 p-2 rounded border border-chrome-700/60 flex flex-col items-center">
                    <div className="text-2xs text-chrome-400">{p}</div>
                    <div className="tabular font-mono font-bold text-chrome-100">
                      {value}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Environmental Data Status */}
            <div className={`bg-chrome-700/20 border ${data.data_quality === 'HIGH' ? 'border-emerald-700/50' : data.data_quality === 'MODERATE' ? 'border-amber-700/50' : 'border-rose-700/50'} rounded p-3 space-y-3`}>
              <div className={`flex items-center gap-2 text-xs font-medium ${data.data_quality === 'HIGH' ? 'text-emerald-400' : data.data_quality === 'MODERATE' ? 'text-amber-400' : 'text-rose-400'}`}>
                {data.data_quality === 'HIGH' || data.data_quality === 'MODERATE' ? 'Environmental Data: All required inputs available ✓' :
                 'Environmental Data: Spatiotemporal fallback used ⚠'}
              </div>
              
              {data.data_quality === 'LIMITED' && (
                <div className="text-2xs text-chrome-300 leading-snug">
                  Satellite observation unavailable; a validated spatiotemporal fallback was used.
                  {['AOD', 'NO2'].some(k => data.satellite_provenance[k]?.source === 'spatiotemporal_gapfill') && (
                    <div className="text-rose-300 mt-1 italic">
                      Limited data quality: spatial reconstruction may underestimate localized pollution extremes.
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-1.5 border-t border-chrome-700/50 pt-2">
                {Object.entries(data.satellite_provenance)
                  .filter(([key]) => key !== 'VWS' && key !== 'Synthetic VWS')
                  .map(([key, prov]) => (
                  <div key={key} className="flex justify-between items-center text-2xs">
                    <span className="text-chrome-300 font-medium">{key}</span>
                    {prov.source === 'observed' || prov.source === 'temporal_recovery' ? (
                      <span className="text-emerald-400 flex items-center gap-1">
                        ✓ Available
                      </span>
                    ) : prov.source === 'ml_gapfilled' ? (
                      <span className="text-rose-400 flex items-center gap-1">
                        ⚠ ML estimate
                      </span>
                    ) : (
                      <span className="text-rose-400 flex items-center gap-1">
                        ⚠ Spatiotemporal estimate
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
