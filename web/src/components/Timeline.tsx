import React from 'react'

interface TimelineProps {
  dates: string[]
  selectedDate: string
  onDateSelect: (date: string) => void
  noCoverageDates?: Set<string>
}

export const Timeline: React.FC<TimelineProps> = ({
  dates,
  selectedDate,
  onDateSelect,
  noCoverageDates = new Set(),
}) => {
  return (
    <div
      className="bg-chrome-900/90 backdrop-blur border-t border-chrome-700 px-4 py-2 flex flex-col gap-1.5 select-none"
      role="region"
      aria-label="Date timeline"
    >
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span className="text-chrome-300 font-sans font-medium">Timeline:</span>
          <span className="tabular text-chrome-100 font-mono font-semibold bg-chrome-700 px-2 py-0.5 rounded">
            {selectedDate}
          </span>
          {noCoverageDates.has(selectedDate) && (
            <span className="text-2xs text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">
              Low/Partial Satellite Retrieval
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-2xs text-chrome-300">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> Coverage
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-slate-500" /> Cloud Gap
          </span>
        </div>
      </div>

      {/* Scrubbable tick bar */}
      <div className="relative w-full h-8 flex items-center overflow-x-auto py-1 space-x-1 no-scrollbar">
        {dates.map((d) => {
          const isSelected = d === selectedDate
          const hasGap = noCoverageDates.has(d)

          return (
            <button
              key={d}
              onClick={() => onDateSelect(d)}
              title={hasGap ? `${d} (Coverage Gap)` : d}
              className={[
                'h-6 flex-1 min-w-[6px] max-w-[14px] rounded-xs transition-all relative group',
                isSelected
                  ? 'bg-sky-400 ring-2 ring-sky-300 ring-offset-1 ring-offset-chrome-900 z-10'
                  : hasGap
                  ? 'bg-chrome-700/60 hover:bg-chrome-500'
                  : 'bg-chrome-500 hover:bg-chrome-300',
              ].join(' ')}
              aria-label={`Date ${d}`}
              aria-pressed={isSelected}
            >
              {/* Tooltip on hover */}
              <span className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 hidden group-hover:block bg-chrome-900 border border-chrome-700 text-chrome-100 text-2xs px-1.5 py-0.5 rounded tabular whitespace-nowrap pointer-events-none z-20">
                {d}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
