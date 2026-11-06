import React from 'react'
import { LayerKey } from '../types/api'

interface LayerSwitcherProps {
  selectedLayer: LayerKey
  onLayerSelect: (layer: LayerKey) => void
  showGrid?: boolean
  onToggleGrid?: (show: boolean) => void
}

const LAYERS: { id: LayerKey; label: string; desc: string }[] = [
  { id: 'aqi', label: 'Composite AQI', desc: 'CPCB standard 6-pollutant max sub-index' },
  { id: 'pm25', label: 'PM2.5', desc: 'Fine inhalable particles (µg/m³)' },
  { id: 'pm10', label: 'PM10', desc: 'Coarse particulate matter (µg/m³)' },
  { id: 'no2', label: 'NO2', desc: 'Nitrogen dioxide (µg/m³)' },
  { id: 'so2', label: 'SO2', desc: 'Sulphur dioxide (µg/m³)' },
  { id: 'co', label: 'CO', desc: 'Carbon monoxide (mg/m³)' },
  { id: 'o3', label: 'Ozone', desc: 'Surface ozone (µg/m³)' },
  { id: 'hcho', label: 'HCHO Column', desc: 'Formaldehyde tropospheric column (mol/m²)' },
]

export const LayerSwitcher: React.FC<LayerSwitcherProps> = ({
  selectedLayer,
  onLayerSelect,
}) => {
  return (
    <div
      className="bg-chrome-900/90 backdrop-blur border border-chrome-700 rounded p-2.5 shadow-lg text-xs font-sans pointer-events-auto w-48"
      aria-label="Layer Switcher"
    >

      <div className="font-semibold text-chrome-300 text-2xs uppercase tracking-wider mb-2">
        Active Layer
      </div>

      <div className="flex flex-col gap-1">
        {LAYERS.map(({ id, label }) => {
          const isSelected = selectedLayer === id
          return (
            <button
              key={id}
              onClick={() => onLayerSelect(id)}
              className={[
                'px-2.5 py-1.5 rounded text-left flex items-center justify-between text-xs transition-colors',
                isSelected
                  ? 'bg-chrome-700 text-chrome-100 font-semibold border-l-2 border-sky-400'
                  : 'text-chrome-300 hover:text-chrome-100 hover:bg-chrome-700/50',
              ].join(' ')}
            >
              <span>{label}</span>
              {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />}
            </button>
          )
        })}
      </div>
    </div>
  )
}
