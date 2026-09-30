# Antigravity prompt

Put `SPEC.md` at the repo root first, then use these. Prompt 0 is one-time setup.
Prompts 1-8 map to the build order in the spec — run them one at a time, verify
each in the browser before moving on. Do not paste them all at once.

---

## Prompt 0 — scaffold and contract

```
Read SPEC.md at the repo root in full before doing anything. It is the binding
specification for this project; where this message and SPEC.md disagree, SPEC.md wins.

Set up the project skeleton only. Do not build any screens yet.

Backend (/api directory):
- FastAPI app, DuckDB for the pre-computed prediction store.
- Implement all five endpoints from SPEC.md section 3, returning data read from
  DuckDB/Parquet. Never load a model in a request handler.
- Put CPCB sub-index breakpoint logic in a single module, aqi/breakpoints.py, with
  unit tests. This is the only place AQI is computed anywhere in the codebase.
- Seed a realistic fixture dataset so the frontend can be built before real
  predictions are wired in: ~200x200 grid cells, 90 days, six pollutants, roughly
  15% of cells/days marked as no-coverage so gap handling gets exercised from day one.
  Put the fixture generator in a clearly named script; it must be trivial to delete.
- CORS for the dev frontend, a /health route, response caching on the read endpoints.

Frontend (/web directory):
- React 18 + TypeScript + Vite, Tailwind, MapLibre GL, Recharts, TanStack Query.
- Generate TypeScript types from the API contract in SPEC.md section 3 and keep
  them in one shared types module.
- Set up design tokens in the Tailwind config: the CPCB AQI scale exactly as given
  in SPEC.md section 6, plus the cool desaturated chrome palette.

Before writing frontend code, produce a short design plan per SPEC.md section 6:
4-6 named hex values for the chrome palette, the two typefaces and their roles, a
one-paragraph layout concept with an ASCII wireframe of the map view. Review that
plan against the "Avoid" list in section 6 and tell me what you changed and why.
Wait for my approval on the plan before building.

Also add: docker-compose for both services, a README with local setup, and
.env.example. No auth.
```

---

## Prompt 1 — map and legend

```
Build step 1 from SPEC.md section 9 only: the map view rendering a single AQI
layer for a single hardcoded date, with the permanent legend.

- Full-bleed MapLibre map, muted basemap so the AQI layer carries the colour.
- AQI rendered as discrete stepped bands at the CPCB breakpoints. Do not use a
  smooth interpolated colour ramp — verify visually that the boundary between
  Moderate and Poor is a hard edge.
- No-coverage cells use the hatch treatment from SPEC.md, clearly distinct from
  the Good band. Show me a screenshot proving low-AQI and no-coverage are not
  confusable.
- Permanent legend with category names as text, not colour swatches alone.

Stop after this. No date control, no clicking, no other layers.
```

---

## Prompt 2 — timeline and layers

```
Add step 2: the date timeline and layer switching.

- Scrubbable timeline along the bottom of the map. Dates with no satellite
  coverage are marked on the track itself so gaps are visible before selection.
- Layer switch: AQI (default), individual pollutant sub-index, HCHO column,
  hotspot overlay, fire points. AQI and pollutant are mutually exclusive; the
  others stack.
- Layer changes crossfade. No other motion.
- View state goes in the URL: ?lat=&lon=&date=&layer=. Reloading restores the view.
```

---

## Prompt 3 — location detail panel

```
Add step 3: click-anywhere opens the location detail panel, wired to /api/aqi.

Per SPEC.md 4.2:
- Overlay panel, does not navigate away from the map.
- AQI value, category, dominant pollutant.
- All six sub-indices as horizontal bars, each coloured by its own category,
  dominant one marked.
- Concentrations with confidence intervals shown, not hidden behind a toggle.
- Distance to nearest station and that station's observed value when available.
  Give this real prominence — it is the trust signal.
- coverage: "none" renders an explicit no-data state explaining that satellite
  retrieval failed for this cell and date, with a suggestion to try a nearby date.
  It must not render as zero or as an error.

Panel open/close is animated. Nothing else on the page animates.
```

---

## Prompt 4 — time series

```
Add step 4: the time series, both the 30-day mini chart in the detail panel and
the expanded full-range view.

- Confidence interval as a band around the line.
- Null values break the line; do not connect across a gap. Mark gap regions
  distinctly on the x-axis.
- Variable selector: AQI or any individual pollutant or HCHO column.
- Tabular figures on all axis labels and tooltips, decimal-aligned.
```

---

## Prompt 5 — stations

```
Add step 5: station markers.

- Always visible on the map, visually distinct from grid data without needing
  the legend.
- Clicking a station shows observed vs predicted AQI for the selected date, with
  the difference stated plainly.
- Where a station observation exists, it is labelled as measured and the model
  value as estimated. A user must never be unsure which number is which.
```

---

## Prompt 6 — HCHO hotspots

```
Build the HCHO hotspots page per SPEC.md 4.3, at route /hotspots.

- Hotspot polygons with opacity keyed to Gi* significance, over the same basemap.
- Season selector.
- Side panel with the ranked cluster table: location, mean HCHO, seasonality,
  dominant driver, fire correlation.
- One chart: lagged correlation of HCHO against fire count at lags 0 through 3 days.
- Simplify GeoJSON geometry before it reaches the browser. If the payload exceeds
  a few MB, move the simplification server-side and tell me.
```

---

## Prompt 7 — validation page

```
Build the validation page per SPEC.md 4.4 at route /validation. This page is the
scientific argument for the project, so give it room and do not compress it into
a grid of equal cards.

- Observed vs predicted scatter with the 1:1 line drawn, large enough to inspect
  individual points, filterable by pollutant.
- Per-pollutant metrics table: R2, RMSE, MAE, n. Decimal-aligned tabular figures.
- Leave-one-station-out table sorted worst-first by default.
- AQI category confusion matrix.
- Residual distribution.

Read the page as a sequence of arguments, not a dashboard. Add short plain-language
captions saying what each panel demonstrates.
```

---

## Prompt 8 — method page and quality pass

```
Final step.

1. Build the method page at /method: data sources, model structure, how AQI is
   derived from predicted concentrations, and a limitations section covering
   monsoon cloud-gap loss, HCHO signal-to-noise at daily resolution, and
   extrapolation beyond the training station footprint. Written for a reviewer
   who has not read the paper. Do not oversell.

2. Quality pass against SPEC.md section 7:
   - responsive to tablet; detail panel becomes a bottom sheet on phone
   - visible keyboard focus everywhere; map layer and date controls keyboard-operable
   - prefers-reduced-motion respected
   - every colour-coded classification also carries its category name as text
   - real loading, empty and error states throughout

3. Self-critique pass: screenshot each screen, review against the "Avoid" list in
   SPEC.md section 6, and remove one thing per screen that is decoration rather
   than information. Report what you removed.
```

---

## Notes on driving this

- Give Antigravity one prompt per turn. Long multi-screen prompts produce a
  plausible-looking app where the hard parts (coverage gaps, discrete colour
  bands, CI display) are quietly skipped.
- The three things to check yourself after every step, because they are the ones
  most likely to be silently wrong: (1) the AQI colour scale is stepped, not a
  gradient; (2) no-coverage never renders as a value; (3) no breakpoint arithmetic
  has crept into the frontend.
- Swap the fixture generator for your real prediction store as soon as step 3
  works. Building the whole UI against synthetic data hides shape mismatches.
