import React from 'react'
import { AQICategory, AQI_COLORS, AQI_BREAKPOINTS } from '../types/api'

const CATEGORIES: AQICategory[] = [
  'Good',
  'Satisfactory',
  'Moderate',
  'Poor',
  'Very Poor',
  'Severe'
]

export const Legend: React.FC = () => {
  return (
    <div
      className="bg-chrome-900/90 backdrop-blur border border-chrome-700 rounded p-3 shadow-lg text-xs font-sans select-none pointer-events-auto"
      aria-label="CPCB AQI Legend"
    >
      <div className="font-semibold text-chrome-100 mb-2 tracking-wide uppercase text-2xs text-chrome-300">
        CPCB Air Quality Index
      </div>

      <div className="space-y-1.5">
        {CATEGORIES.map((cat) => {
          const [min, max] = AQI_BREAKPOINTS[cat]
          const color = AQI_COLORS[cat]
          return (
            <div key={cat} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span
                  className="w-3.5 h-3.5 rounded-sm border border-chrome-700 shrink-0"
                  style={{ backgroundColor: color }}
                />
                <span className="text-chrome-100 font-medium">{cat}</span>
              </div>
              <span className="tabular text-chrome-300 text-2xs">
                {min}–{max}
              </span>
            </div>
          )
        })}

        {/* No coverage explicitly marked with diagonal hatch styling */}
        <div className="flex items-center justify-between gap-3 pt-1 border-t border-chrome-700/60 mt-1.5">
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-3.5 rounded-sm aqi-no-coverage-hatch border border-chrome-700 shrink-0" />
            <span className="text-chrome-300 font-medium">No coverage</span>
          </div>
          <span className="text-chrome-500 text-2xs italic">satellite gap</span>
        </div>
      </div>
    </div>
  )
}
