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
      className="relative w-80 max-w-[calc(100vw-2rem)] bg-chrome-900/95 backdrop-blur-md border border-chrome-700 rounded shadow-2xl flex flex-col transition-all duration-300 font-sans"
      role="dialog"
      aria-labelledby="prediction-detail-heading"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-chrome-700/80 bg-chrome-900">
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

      <div className="p-4 space-y-4">
        {isLoading ? (
          <div className="text-chrome-300 text-xs py-8 text-center animate-pulse">
            Loading prediction...
          </div>
        ) : error ? (
          (() => {
            try {
              const errObj = JSON.parse(error)
              if (errObj.type === 'MISSING_DATA') {
                return (
                  <div className="bg-chrome-700/30 border border-chrome-700 rounded p-4 text-left space-y-4">
                    <div className="text-sm font-semibold text-amber-400 text-center border-b border-chrome-700/50 pb-2">
                      Environmental Data Status
                    </div>
                    <p className="text-xs text-chrome-300 text-center">
                      Environmental data is unavailable for this location/date.
                    </p>
                    
                    <div>
                      <div className="text-xs font-semibold text-rose-400 mb-2">
                        ✕ Missing data
                      </div>
                      <div className="space-y-2 text-xs pl-1">
                        {errObj.missing_data.map((src: any) => (
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

                    {errObj.available_data && errObj.available_data.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-emerald-400 mb-2 border-t border-chrome-700/50 pt-3">
                          ✓ Available data
                        </div>
                        <div className="space-y-2 text-xs pl-1">
                          {errObj.available_data.map((src: any) => (
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
            <div className="bg-chrome-700/20 border border-chrome-700 rounded p-3">
              <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
                Environmental Data: All required inputs available ✓
              </div>
            </div>

            {/* Provenance */}
            <div className="bg-chrome-700/20 border border-chrome-700 rounded p-2.5 space-y-1">
              <div className="text-2xs font-semibold text-chrome-300 uppercase tracking-wider">
                Data Provenance
              </div>
              <div className="text-xs text-chrome-300 flex justify-between">
                <span>VWS source:</span>
                <span className="font-mono text-sky-400 capitalize">{data.provenance.vws.source.replace('_', ' ')}</span>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
