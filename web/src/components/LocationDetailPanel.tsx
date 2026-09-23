import React, { useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { AQIResponse, TimeseriesPoint, TimeseriesVariable } from '../types/api'

interface LocationDetailPanelProps {
  data: AQIResponse | null
  isLoading: boolean
  onClose: () => void
}

export const LocationDetailPanel: React.FC<LocationDetailPanelProps> = ({
  data,
  isLoading,
  onClose,
}) => {
  const [selectedVar, setSelectedVar] = useState<TimeseriesVariable>('aqi')
  const [timeseriesData, setTimeseriesData] = useState<TimeseriesPoint[]>([])
  const [tsLoading, setTsLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  // Fetch timeseries when location changes or variable changes
  React.useEffect(() => {
    if (!data) return

    setTsLoading(true)
    const [from, to] = getSurroundingDates(data.date, expanded ? 45 : 15)

    fetch(
      `/api/timeseries?lat=${data.lat}&lon=${data.lon}&from=${from}&to=${to}&variable=${selectedVar}`
    )
      .then((res) => res.json())
      .then((pts: TimeseriesPoint[]) => {
        setTimeseriesData(pts)
        setTsLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load timeseries:', err)
        setTsLoading(false)
      })
  }, [data?.lat, data?.lon, data?.date, selectedVar, expanded])

  if (!data && !isLoading) return null

  return (
    <div
      className="relative w-96 max-w-[calc(100vw-2rem)] bg-chrome-900/95 backdrop-blur-md border border-chrome-700 rounded shadow-2xl flex flex-col max-h-[calc(100vh-8rem)] overflow-hidden transition-all duration-300 font-sans"
      role="dialog"
      aria-labelledby="location-detail-heading"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-chrome-700/80 bg-chrome-900">
        <div>
          <h2 id="location-detail-heading" className="text-sm font-semibold text-chrome-100">
            Location Analysis
          </h2>
          <div className="tabular text-chrome-300 text-2xs font-mono">
            {data ? `${data.lat.toFixed(2)}°N, ${data.lon.toFixed(2)}°E • Cell [${data.grid_cell.join(', ')}]` : 'Loading…'}
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-chrome-500 hover:text-chrome-100 p-1 rounded hover:bg-chrome-700"
          aria-label="Close location detail panel"
        >
          ✕
        </button>
      </div>

      <div className="p-4 overflow-y-auto space-y-4">
        {isLoading ? (
          <div className="text-chrome-300 text-xs py-8 text-center animate-pulse">
            Retrieving cell predictions from store…
          </div>
        ) : !data ? null : data.coverage === 'none' ? (
          /* Explicit No-Coverage State (SPEC.md 4.2 / Rule 3) */
          <div className="bg-chrome-700/30 border border-chrome-700 rounded p-4 text-center space-y-2">
            <div className="w-10 h-10 mx-auto rounded aqi-no-coverage-hatch border border-chrome-500/50" />
            <div className="text-sm font-semibold text-chrome-100">
              No Satellite Retrieval
            </div>
            <p className="text-xs text-chrome-300 leading-relaxed">
              Cloud cover or satellite orbit gap prevented aerosol retrieval for this cell on{' '}
              <span className="tabular font-mono text-chrome-100">{data.date}</span>.
            </p>
            <p className="text-2xs text-chrome-500">
              Try scrub-selecting adjacent dates on the timeline below.
            </p>
          </div>
        ) : (
          <>
            {/* Primary AQI Readout */}
            <div className="flex items-center justify-between bg-chrome-700/30 border border-chrome-700 rounded p-3">
              <div>
                <div className="text-3xl font-bold text-chrome-100 tabular font-mono">
                  {data.aqi}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: data.category_color || '#6B7280' }}
                  />
                  <span className="text-xs font-semibold text-chrome-100">
                    {data.category}
                  </span>
                </div>
              </div>

              <div className="text-right">
                <div className="text-2xs text-chrome-500 uppercase tracking-wider">
                  Dominant Driver
                </div>
                <div className="text-sm font-semibold text-amber-400 font-mono">
                  {data.dominant_pollutant}
                </div>
                <div className="text-2xs text-chrome-300 capitalize mt-0.5">
                  Coverage: {data.coverage}
                </div>
              </div>
            </div>

            {/* Sub-indices Horizontal Bar Chart */}
            <div className="space-y-2">
              <div className="text-2xs font-semibold text-chrome-300 uppercase tracking-wider">
                Sub-indices Breakdown
              </div>
              <div className="space-y-1.5 text-xs">
                {Object.entries(data.sub_indices).map(([pollutant, val]) => {
                  if (val === null || val === undefined) return null
                  const isDominant = pollutant === data.dominant_pollutant
                  const barWidth = Math.min(100, (val / 500) * 100)

                  return (
                    <div key={pollutant} className="space-y-0.5">
                      <div className="flex justify-between text-2xs">
                        <span className={isDominant ? 'font-bold text-amber-300' : 'text-chrome-300'}>
                          {pollutant} {isDominant && '★'}
                        </span>
                        <span className="tabular font-mono text-chrome-100">{val}</span>
                      </div>
                      <div className="h-1.5 w-full bg-chrome-700 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${barWidth}%`,
                            backgroundColor: isDominant ? '#F29C33' : '#38BDF8',
                          }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Concentrations with Confidence Intervals (SPEC.md 4.2 / Rule 4) */}
            <div className="space-y-2">
              <div className="text-2xs font-semibold text-chrome-300 uppercase tracking-wider">
                Estimated Concentrations (95% CI)
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(data.concentrations).map(([p, conc]) => {
                  if (!conc) return null
                  return (
                    <div key={p} className="bg-chrome-700/40 p-2 rounded border border-chrome-700/60">
                      <div className="text-2xs text-chrome-300 font-medium">{p}</div>
                      <div className="tabular font-mono font-semibold text-chrome-100 text-sm">
                        {conc.value.toFixed(1)}{' '}
                        <span className="text-2xs font-normal text-chrome-500">{conc.unit}</span>
                      </div>
                      <div className="text-2xs text-chrome-500 tabular font-mono mt-0.5">
                        [{conc.ci_low.toFixed(1)} – {conc.ci_high.toFixed(1)}]
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Nearest Ground Station Trust Signal (SPEC.md 4.2) */}
            <div className="bg-chrome-700/20 border border-chrome-700 rounded p-2.5 space-y-1">
              <div className="text-2xs font-semibold text-chrome-300 uppercase tracking-wider">
                Nearest Monitoring Station
              </div>
              {data.nearest_station ? (
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-chrome-100">{data.nearest_station.name}</div>
                    <div className="text-2xs text-chrome-500 tabular font-mono">
                      ID: {data.nearest_station.id}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xs text-chrome-300">Distance</div>
                    <div className="tabular font-mono font-semibold text-sky-400">
                      {data.nearest_station.distance_km} km
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-2xs text-chrome-500 italic">No station within search radius</div>
              )}
            </div>

            {/* Mini Time Series Chart with CI Band & Null Gaps (Prompt 4) */}
            <div className="space-y-2 pt-2 border-t border-chrome-700/60">
              <div className="flex items-center justify-between">
                <div className="text-2xs font-semibold text-chrome-300 uppercase tracking-wider">
                  Trend ({expanded ? '90 Days' : '30 Days'})
                </div>
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="text-2xs text-sky-400 hover:text-sky-300"
                >
                  {expanded ? 'Collapse' : 'Expand full range'}
                </button>
              </div>

              {/* Variable Selector */}
              <div className="flex items-center gap-1 overflow-x-auto pb-1 no-scrollbar text-2xs">
                {(['aqi', 'pm25', 'pm10', 'no2', 'so2', 'co', 'o3', 'hcho'] as TimeseriesVariable[]).map(
                  (v) => (
                    <button
                      key={v}
                      onClick={() => setSelectedVar(v)}
                      className={[
                        'px-2 py-0.5 rounded uppercase font-mono transition-colors',
                        selectedVar === v
                          ? 'bg-sky-500 text-white font-bold'
                          : 'bg-chrome-700 text-chrome-300 hover:bg-chrome-500',
                      ].join(' ')}
                    >
                      {v}
                    </button>
                  )
                )}
              </div>

              {/* Chart container */}
              <div className="h-36 w-full pt-2">
                {tsLoading ? (
                  <div className="h-full flex items-center justify-center text-xs text-chrome-500 animate-pulse">
                    Loading trend…
                  </div>
                ) : timeseriesData.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-chrome-500">
                    No series points available
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={timeseriesData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                      <XAxis
                        dataKey="date"
                        tick={{ fill: '#8CA3B8', fontSize: 9 }}
                        tickFormatter={(d: string) => d.slice(5)}
                      />
                      <YAxis tick={{ fill: '#8CA3B8', fontSize: 9 }} domain={['auto', 'auto']} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0F172A',
                          borderColor: '#334155',
                          borderRadius: 4,
                          fontSize: 11,
                        }}
                        labelFormatter={(l) => `Date: ${l}`}
                        formatter={(val: any, name: any) => [
                          val !== null && val !== undefined ? Number(val).toFixed(1) : 'No coverage (null)',
                          name,
                        ]}
                      />
                      {/* CI Band (where available) */}
                      <Line
                        type="monotone"
                        dataKey="ci_high"
                        stroke="#38BDF8"
                        strokeDasharray="2 2"
                        strokeOpacity={0.3}
                        dot={false}
                        connectNulls={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="ci_low"
                        stroke="#38BDF8"
                        strokeDasharray="2 2"
                        strokeOpacity={0.3}
                        dot={false}
                        connectNulls={false}
                      />
                      {/* Value line breaks across gaps */}
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#38BDF8"
                        strokeWidth={2}
                        dot={{ r: 2, fill: '#38BDF8' }}
                        connectNulls={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function getSurroundingDates(centerDateStr: string, radiusDays: number): [string, string] {
  const d = new Date(centerDateStr)
  const from = new Date(d)
  from.setDate(from.getDate() - radiusDays)
  const to = new Date(d)
  to.setDate(to.getDate() + radiusDays)
  return [from.toISOString().slice(0, 10), to.toISOString().slice(0, 10)]
}
