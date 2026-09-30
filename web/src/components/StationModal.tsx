import React from 'react'
import { StationFeature } from '../types/api'

interface StationModalProps {
  station: StationFeature | null
  onClose: () => void
}

export const StationModal: React.FC<StationModalProps> = ({ station, onClose }) => {
  if (!station) return null

  return (
    <div
      className="fixed inset-0 z-modal bg-chrome-900/60 backdrop-blur-xs flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-chrome-900 border border-chrome-700 rounded-lg p-5 max-w-md w-full shadow-2xl space-y-4 font-sans"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="station-modal-title"
      >
        <div className="flex items-start justify-between border-b border-chrome-700/80 pb-3">
          <div>
            <h3 id="station-modal-title" className="text-base font-semibold text-chrome-100">
              {station.name}
            </h3>
            <div className="tabular text-chrome-300 text-2xs font-mono">
              Station ID: {station.station_id} • Lat: {station.lat.toFixed(3)}, Lon: {station.lon.toFixed(3)}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-chrome-500 hover:text-chrome-100 p-1 rounded hover:bg-chrome-700"
            aria-label="Close station modal"
          >
            ✕
          </button>
        </div>

        <div className="text-xs text-chrome-300">
          Validation reading for date: <span className="font-mono text-chrome-100 font-semibold">{station.date}</span>
        </div>

        {/* Observed vs Predicted (SPEC.md 4.1 / Rule 5) */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-chrome-700/30 border border-emerald-700/40 rounded p-3 text-center">
            <div className="text-2xs text-emerald-400 font-semibold uppercase tracking-wider">
              Measured (Observed)
            </div>
            <div className="text-3xl font-bold font-mono text-chrome-100 mt-1">
              {station.observed_aqi !== null ? station.observed_aqi : 'Offline'}
            </div>
            <div className="text-2xs text-chrome-500 mt-0.5">Physical Ground Sensor</div>
          </div>

          <div className="bg-chrome-700/30 border border-sky-700/40 rounded p-3 text-center">
            <div className="text-2xs text-sky-400 font-semibold uppercase tracking-wider">
              Estimated (Model)
            </div>
            <div className="text-3xl font-bold font-mono text-chrome-100 mt-1">
              {station.predicted_aqi !== null ? station.predicted_aqi : 'No Pred'}
            </div>
            <div className="text-2xs text-chrome-500 mt-0.5">Stacked Stacking Model</div>
          </div>
        </div>

        {/* Stated Difference Plainly */}
        <div className="bg-chrome-700/20 border border-chrome-700 rounded p-3 flex items-center justify-between text-xs">
          <span className="text-chrome-300">Model Estimation Bias (Pred - Obs):</span>
          <span
            className={[
              'tabular font-mono font-bold text-sm',
              station.bias === null
                ? 'text-chrome-500'
                : station.bias > 0
                ? 'text-amber-400'
                : station.bias < 0
                ? 'text-sky-400'
                : 'text-emerald-400',
            ].join(' ')}
          >
            {station.bias !== null ? (station.bias > 0 ? `+${station.bias}` : `${station.bias}`) : 'N/A'}{' '}
            AQI points
          </span>
        </div>

        <div className="text-2xs text-chrome-500 italic">
          Observed values are published by central/state monitoring boards; estimated values are derived from satellite retrievals and meteorological inputs.
        </div>
      </div>
    </div>
  )
}
