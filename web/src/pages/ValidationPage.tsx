import React, { useEffect, useState } from 'react'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { ValidationResponse, Pollutant } from '../types/api'

export const ValidationPage: React.FC = () => {
  const [data, setData] = useState<ValidationResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [selectedPollutant, setSelectedPollutant] = useState<Pollutant | 'ALL'>('ALL')

  useEffect(() => {
    setLoading(true)
    fetch('/api/validation')
      .then((res) => res.json())
      .then((res: ValidationResponse) => {
        setData(res)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load validation data:', err)
        setLoading(false)
      })
  }, [])

  if (loading || !data) {
    return (
      <div className="flex h-full items-center justify-center font-sans text-chrome-300 text-sm animate-pulse">
        Computing validation statistics against monitoring station ground truth…
      </div>
    )
  }

  // Filter scatter data by pollutant
  const filteredScatter =
    selectedPollutant === 'ALL'
      ? data.scatter.slice(0, 500)
      : data.scatter.filter((s) => s.pollutant === selectedPollutant).slice(0, 500)

  return (
    <div className="h-full overflow-y-auto bg-chrome-900 text-chrome-100 p-6 space-y-8 font-sans max-w-6xl mx-auto">
      {/* Page Title & Preamble */}
      <header className="space-y-1">
        <h1 className="text-xl font-bold text-chrome-100 tracking-tight">
          Model Validation & Ground-Truth Performance
        </h1>
        <p className="text-xs text-chrome-300 max-w-3xl leading-relaxed">
          Independent evaluation of stacked regression ensembles against physical Central Pollution
          Control Board (CPCB) monitoring stations across India. Model estimates are evaluated
          using leave-one-station-out cross-validation to assess spatial generalisation.
        </p>
      </header>

      {/* Summary Metrics Bar */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-chrome-700/30 border border-chrome-700 rounded p-3 text-center">
          <div className="text-2xs text-chrome-300 uppercase tracking-wider">Overall R² Score</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            {data.overall.r2.toFixed(3)}
          </div>
          <div className="text-2xs text-chrome-500 mt-0.5">Coefficient of Determination</div>
        </div>

        <div className="bg-chrome-700/30 border border-chrome-700 rounded p-3 text-center">
          <div className="text-2xs text-chrome-300 uppercase tracking-wider">Root Mean Square Error</div>
          <div className="text-2xl font-bold font-mono text-sky-400 mt-1">
            {data.overall.rmse.toFixed(1)}
          </div>
          <div className="text-2xs text-chrome-500 mt-0.5">RMSE (AQI points)</div>
        </div>

        <div className="bg-chrome-700/30 border border-chrome-700 rounded p-3 text-center">
          <div className="text-2xs text-chrome-300 uppercase tracking-wider">Mean Absolute Error</div>
          <div className="text-2xl font-bold font-mono text-sky-400 mt-1">
            {data.overall.mae.toFixed(1)}
          </div>
          <div className="text-2xs text-chrome-500 mt-0.5">MAE (AQI points)</div>
        </div>

        <div className="bg-chrome-700/30 border border-chrome-700 rounded p-3 text-center">
          <div className="text-2xs text-chrome-300 uppercase tracking-wider">Sample Size</div>
          <div className="text-2xl font-bold font-mono text-chrome-100 mt-1">
            {data.overall.n.toLocaleString()}
          </div>
          <div className="text-2xs text-chrome-500 mt-0.5">Paired Station-Days</div>
        </div>
      </section>

      {/* Argument 1: Scatter plot with 1:1 line */}
      <section className="space-y-2 bg-chrome-700/20 border border-chrome-700 rounded p-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-chrome-700 pb-2">
          <div>
            <h2 className="text-sm font-semibold text-chrome-100">
              1. Observed vs Predicted Scatter (1:1 Reference Line)
            </h2>
            <p className="text-2xs text-chrome-300">
              Demonstrates lack of systematic under/over-estimation across the dynamic range.
            </p>
          </div>

          {/* Pollutant Filter */}
          <div className="flex items-center gap-1 text-2xs">
            <span className="text-chrome-500 mr-1">Filter:</span>
            {(['ALL', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3'] as const).map((pol) => (
              <button
                key={pol}
                onClick={() => setSelectedPollutant(pol)}
                className={[
                  'px-2 py-0.5 rounded font-mono transition-colors',
                  selectedPollutant === pol
                    ? 'bg-sky-500 text-white font-bold'
                    : 'bg-chrome-700 text-chrome-300 hover:bg-chrome-500',
                ].join(' ')}
              >
                {pol}
              </button>
            ))}
          </div>
        </div>

        <div className="h-80 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
              <XAxis
                type="number"
                dataKey="observed"
                name="Observed"
                tick={{ fill: '#8CA3B8', fontSize: 10 }}
                domain={[0, 400]}
                label={{ value: 'Observed Sensor Value', position: 'insideBottom', offset: -10, fill: '#8CA3B8', fontSize: 11 }}
              />
              <YAxis
                type="number"
                dataKey="predicted"
                name="Predicted"
                tick={{ fill: '#8CA3B8', fontSize: 10 }}
                domain={[0, 400]}
                label={{ value: 'Predicted Model Value', angle: -90, position: 'insideLeft', fill: '#8CA3B8', fontSize: 11 }}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', fontSize: 11 }}
                formatter={(v: any) => [Number(v).toFixed(1), 'Value']}
              />
              {/* 1:1 Identity Reference Line */}
              <ReferenceLine
                segment={[{ x: 0, y: 0 }, { x: 400, y: 400 }]}
                stroke="#64748B"
                strokeWidth={1.5}
                strokeDasharray="3 3"
                label={{ value: '1:1 Ideal', fill: '#64748B', position: 'top', fontSize: 10 }}
              />
              <Scatter
                name="Validation Observations"
                data={filteredScatter}
                fill="#38BDF8"
                fillOpacity={0.6}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Argument 2: Per-pollutant metrics table */}
      <section className="space-y-2 bg-chrome-700/20 border border-chrome-700 rounded p-4">
        <div>
          <h2 className="text-sm font-semibold text-chrome-100">
            2. Per-Pollutant Stacking Performance
          </h2>
          <p className="text-2xs text-chrome-300">
            Metrics calculated independently for each target variable in the stacked ensemble.
          </p>
        </div>

        <div className="border border-chrome-700 rounded overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-chrome-700/50 text-chrome-300 font-semibold">
              <tr>
                <th className="p-2.5">Pollutant</th>
                <th className="p-2.5 tabular text-right">R²</th>
                <th className="p-2.5 tabular text-right">RMSE</th>
                <th className="p-2.5 tabular text-right">MAE</th>
                <th className="p-2.5 tabular text-right">Observations (n)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-chrome-700/40">
              {data.per_pollutant.map((m) => (
                <tr key={m.pollutant} className="hover:bg-chrome-700/30">
                  <td className="p-2.5 font-semibold text-chrome-100 font-mono">{m.pollutant}</td>
                  <td className="p-2.5 tabular font-mono text-right text-emerald-400 font-medium">
                    {m.r2.toFixed(3)}
                  </td>
                  <td className="p-2.5 tabular font-mono text-right text-chrome-100">
                    {m.rmse.toFixed(2)}
                  </td>
                  <td className="p-2.5 tabular font-mono text-right text-chrome-100">
                    {m.mae.toFixed(2)}
                  </td>
                  <td className="p-2.5 tabular font-mono text-right text-chrome-300">
                    {m.n.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Argument 3: Leave-one-station-out cross-validation (Worst-first) */}
      <section className="space-y-2 bg-chrome-700/20 border border-chrome-700 rounded p-4">
        <div>
          <h2 className="text-sm font-semibold text-chrome-100">
            3. Spatial Generalisation: Leave-One-Station-Out (LOSO)
          </h2>
          <p className="text-2xs text-chrome-300">
            Sorted worst-first by default. Stations with lower performance typically suffer from
            microclimate effects or heavy local industrial point sources outside satellite footprint.
          </p>
        </div>

        <div className="border border-chrome-700 rounded overflow-hidden max-h-64 overflow-y-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-chrome-700/50 text-chrome-300 font-semibold sticky top-0">
              <tr>
                <th className="p-2">Station Name</th>
                <th className="p-2">Station ID</th>
                <th className="p-2 tabular text-right">R²</th>
                <th className="p-2 tabular text-right">RMSE</th>
                <th className="p-2 tabular text-right">n</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-chrome-700/40">
              {data.leave_one_station_out.map((stn, idx) => (
                <tr
                  key={stn.station_id}
                  className={idx < 3 ? 'bg-rose-950/20 hover:bg-rose-900/30' : 'hover:bg-chrome-700/30'}
                >
                  <td className="p-2 font-medium text-chrome-100">{stn.name}</td>
                  <td className="p-2 font-mono text-2xs text-chrome-500">{stn.station_id}</td>
                  <td
                    className={[
                      'p-2 tabular font-mono text-right font-medium',
                      stn.r2 < 0.8 ? 'text-amber-400' : 'text-emerald-400',
                    ].join(' ')}
                  >
                    {stn.r2.toFixed(3)}
                  </td>
                  <td className="p-2 tabular font-mono text-right text-chrome-100">
                    {stn.rmse.toFixed(1)}
                  </td>
                  <td className="p-2 tabular font-mono text-right text-chrome-300">
                    {stn.n}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Argument 4: Category Confusion Matrix */}
      {data.category_confusion && data.category_confusion.labels && (
        <section className="space-y-2 bg-chrome-700/20 border border-chrome-700 rounded p-4">
          <div>
            <h2 className="text-sm font-semibold text-chrome-100">
              4. CPCB Category Classification Matrix
            </h2>
            <p className="text-2xs text-chrome-300">
              Diagonal elements represent exact category matches between physical sensor and satellite prediction.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="text-xs border-collapse font-mono">
              <thead>
                <tr>
                  <th className="p-2 text-2xs text-chrome-500 text-left font-sans">
                    Observed \ Pred
                  </th>
                  {data.category_confusion.labels.map((l) => (
                    <th key={l} className="p-2 text-2xs text-chrome-300 text-center">
                      {l}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.category_confusion.labels.map((rowLabel, rIdx) => (
                  <tr key={rowLabel} className="border-t border-chrome-700/40">
                    <td className="p-2 font-sans font-medium text-chrome-100">{rowLabel}</td>
                    {data.category_confusion.matrix[rIdx]?.map((val, cIdx) => {
                      const isDiagonal = rIdx === cIdx
                      return (
                        <td
                          key={cIdx}
                          className={[
                            'p-2 text-center tabular font-semibold',
                            isDiagonal
                              ? 'bg-emerald-950/40 text-emerald-300'
                              : val > 0
                              ? 'text-chrome-300'
                              : 'text-chrome-500',
                          ].join(' ')}
                        >
                          {val}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
