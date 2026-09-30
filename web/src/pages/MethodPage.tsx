import React from 'react'

export const MethodPage: React.FC = () => {
  return (
    <div className="h-full overflow-y-auto bg-chrome-900 text-chrome-100 p-8 space-y-8 font-sans max-w-4xl mx-auto leading-relaxed">
      <header className="border-b border-chrome-700/80 pb-4">
        <h1 className="text-2xl font-bold text-chrome-100 tracking-tight">
          Methodology & Physical Framework
        </h1>
        <p className="text-xs text-chrome-300 mt-1">
          Technical specifications for satellite retrieval ingestion, stacked ensemble architecture,
          breakpoint conversions, and known operational limitations.
        </p>
      </header>

      {/* 1. Data Sources */}
      <section className="space-y-3">
        <h2 className="text-base font-semibold text-sky-400">1. Data Sources & Retrievals</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="bg-chrome-700/20 border border-chrome-700 rounded p-3">
            <h3 className="font-semibold text-chrome-100">Sentinel-5P TROPOMI</h3>
            <p className="text-chrome-300 mt-1">
              Tropospheric column densities of Formaldehyde (HCHO), Nitrogen Dioxide (NO2),
              Sulphur Dioxide (SO2), and Carbon Monoxide (CO). Level-2 products filtered for cloud
              fraction &lt; 0.3 and quality assurance (qa_value &gt; 0.5).
            </p>
          </div>
          <div className="bg-chrome-700/20 border border-chrome-700 rounded p-3">
            <h3 className="font-semibold text-chrome-100">MODIS & VIIRS AOD</h3>
            <p className="text-chrome-300 mt-1">
              Multi-Angle Implementation of Atmospheric Correction (MAIAC) 1 km Aerosol Optical
              Depth (AOD) at 550 nm, merged across Terra and Aqua platforms to inform surface PM2.5
              and PM10 concentrations.
            </p>
          </div>
          <div className="bg-chrome-700/20 border border-chrome-700 rounded p-3">
            <h3 className="font-semibold text-chrome-100">ERA5 Reanalysis Meteorological Fields</h3>
            <p className="text-chrome-300 mt-1">
              Boundary layer height (BLH), 2-metre temperature, relative humidity, surface pressure,
              and 10-metre u/v wind components representing vertical mixing dynamics and advection.
            </p>
          </div>
          <div className="bg-chrome-700/20 border border-chrome-700 rounded p-3">
            <h3 className="font-semibold text-chrome-100">CPCB Ground Truth Network</h3>
            <p className="text-chrome-300 mt-1">
              Continuous Ambient Air Quality Monitoring Stations (CAAQMS) operated by Central and State
              Pollution Control Boards used exclusively for ensemble calibration and validation.
            </p>
          </div>
        </div>
      </section>

      {/* 2. Model Structure */}
      <section className="space-y-3">
        <h2 className="text-base font-semibold text-sky-400">2. Stacked Regression Ensemble Structure</h2>
        <p className="text-xs text-chrome-300">
          Individual ground concentrations are predicted through independent two-stage stacking
          architectures:
        </p>
        <div className="bg-chrome-700/30 border border-chrome-700 rounded p-4 text-xs space-y-2 font-mono">
          <div>
            <span className="text-amber-400 font-bold">Level 0 (Base Learners):</span>
            <span className="text-chrome-300"> LightGBM regressor + XGBoost regressor + Random Forest</span>
          </div>
          <div>
            <span className="text-sky-400 font-bold">Level 1 (Meta Learner):</span>
            <span className="text-chrome-300"> Ridge regression with non-negative concentration constraints</span>
          </div>
        </div>
        <p className="text-xs text-chrome-300">
          Uncertainty is quantified via conformal quantile regression calibrated across out-of-fold station
          validation predictions, yielding empirical 95% confidence bounds ($ci\_low$, $ci\_high$) for every
          point estimate.
        </p>
      </section>

      {/* 3. AQI Derivation */}
      <section className="space-y-3">
        <h2 className="text-base font-semibold text-sky-400">3. AQI Derivation (CPCB Breakpoints)</h2>
        <p className="text-xs text-chrome-300">
          The composite Air Quality Index is derived strictly following Central Pollution Control Board
          guidelines using linear interpolation between designated concentration intervals:
        </p>
        <div className="bg-chrome-700/20 border border-chrome-700 rounded p-3 text-xs font-mono">
          <code className="text-emerald-400">
            I_p = ((I_high - I_low) / (BP_high - BP_low)) * (C_p - BP_low) + I_low
          </code>
          <div className="text-chrome-300 text-2xs mt-2 font-sans">
            Where <span className="font-mono">AQI = max(I_PM2.5, I_PM10, I_NO2, I_SO2, I_CO, I_O3)</span>.
            The dominant pollutant is defined as the variable reaching the maximum sub-index.
          </div>
        </div>
      </section>

      {/* 4. Limitations (SPEC.md 4.5 / Prompt 8) */}
      <section className="space-y-3 bg-amber-950/20 border border-amber-800/40 rounded p-4">
        <h2 className="text-base font-semibold text-amber-400">4. Known Scientific Limitations</h2>
        <div className="space-y-2 text-xs text-chrome-300">
          <div>
            <span className="font-semibold text-chrome-100">• Monsoon Cloud-Gap Loss:</span> During the
            Southwest Monsoon (June–September), persistent deep convective cloud cover disrupts passive UV/vis
            and SWIR satellite retrievals. Up to 40% of daily grid cells experience missing satellite coverage.
            The system explicitly leaves these as no-coverage hatches rather than interpolating untruthfully.
          </div>
          <div>
            <span className="font-semibold text-chrome-100">• Daily HCHO Signal-to-Noise:</span> Tropospheric
            formaldehyde columns derived from single-day TROPOMI overpasses exhibit standard deviation
            uncertainties on the order of 20–30%. Daily columns are smoothed and spatial Getis-Ord Gi* hot-spots
            are aggregated seasonally to prevent noise artifacts from masquerading as biogenic bursts.
          </div>
          <div>
            <span className="font-semibold text-chrome-100">• Spatial Extrapolation Footprint:</span> Physical
            ground stations are concentrated in urban and peri-urban agglomerations. Regions exceeding 150 km
            from the nearest physical station rely on meteorological and terrain similarity; confidence intervals
            are correspondingly widened.
          </div>
        </div>
      </section>
    </div>
  )
}
