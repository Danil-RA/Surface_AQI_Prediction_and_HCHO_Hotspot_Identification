import type { Config } from 'tailwindcss'

/**
 * Design tokens for the AQI research application.
 *
 * Rules:
 * - AQI scale colours (CPCB standard) are the only saturated colours on the page.
 * - Chrome palette is cool desaturated slate — everything recedes so the data reads.
 * - No brand accent that competes with the AQI ramp.
 * - No warm cream or terracotta.
 */
const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      // ----------------------------------------------------------------
      // Chrome palette — cool desaturated slate
      // ----------------------------------------------------------------
      colors: {
        chrome: {
          900: '#0F172A',  // page background, sidebar
          700: '#334155',  // panel surfaces
          500: '#64748B',  // borders, dividers
          300: '#CBD5E1',  // secondary text
          100: '#F1F5F9',  // primary text on dark
          axis: '#8CA3B8', // axis lines, chart grid lines
        },

        // ----------------------------------------------------------------
        // CPCB AQI scale — published standard, do not modify
        // ----------------------------------------------------------------
        aqi: {
          good:        '#55A84F',  // 0–50
          satisfactory:'#A3C853', // 51–100
          moderate:    '#FFF833',  // 101–200
          poor:        '#F29C33',  // 201–300
          'very-poor': '#E93F33',  // 301–400
          severe:      '#AF2D24',  // 401–500
          'no-coverage':'#6B7280', // diagonal hatch base at 35% opacity
        },
      },

      // ----------------------------------------------------------------
      // Typography
      // ----------------------------------------------------------------
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        // Ensure readout labels stay legible at small sizes
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },

      // ----------------------------------------------------------------
      // Layout
      // ----------------------------------------------------------------
      zIndex: {
        map:    '0',
        legend: '10',
        panel:  '20',
        timeline: '20',
        nav:    '30',
        modal:  '40',
      },
    },
  },
  plugins: [],
}

export default config
