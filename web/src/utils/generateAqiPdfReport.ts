import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'
import { PredictionResponse, AQICategory, Pollutant } from '../types/api'

export interface GeneratePdfReportOptions {
  data: PredictionResponse
  locationName?: string | null
}

// CPCB category background and text colors for PDF rendering (RGB tuples)
const CPCB_PDF_THEME: Record<AQICategory, { bg: [number, number, number]; text: [number, number, number] }> = {
  Good: { bg: [85, 168, 79], text: [255, 255, 255] },
  Satisfactory: { bg: [163, 200, 83], text: [20, 40, 20] },
  Moderate: { bg: [245, 200, 30], text: [30, 30, 20] },
  Poor: { bg: [242, 156, 51], text: [255, 255, 255] },
  'Very Poor': { bg: [233, 63, 51], text: [255, 255, 255] },
  Severe: { bg: [175, 45, 36], text: [255, 255, 255] },
}

// Units mapping for the six CPCB pollutants
const POLLUTANT_UNITS: Record<Pollutant, string> = {
  'PM2.5': 'ug/m3',
  'PM10': 'ug/m3',
  'NO2': 'ug/m3',
  'SO2': 'ug/m3',
  'O3': 'ug/m3',
  'CO': 'mg/m3',
}

const POLLUTANTS_ORDER: Pollutant[] = ['PM2.5', 'PM10', 'NO2', 'SO2', 'O3', 'CO']

/**
 * Sanitizes a string for safe use in file names
 */
export function sanitizeFilename(str: string): string {
  return str.replace(/[^a-zA-Z0-9_-]/g, '_').replace(/_{2,}/g, '_')
}

/**
 * Generates and downloads a clean, professional PDF report for an AQI prediction snapshot.
 */
export async function generateAqiPdfReport({ data, locationName }: GeneratePdfReportOptions): Promise<void> {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  })

  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 12
  const contentWidth = pageWidth - margin * 2
  let currentY = margin

  // -------------------------------------------------------------------------
  // Header Banner
  // -------------------------------------------------------------------------
  doc.setFillColor(15, 23, 42) // slate-900
  doc.rect(margin, currentY, contentWidth, 20, 'F')

  doc.setTextColor(255, 255, 255)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(13)
  doc.text('SURFACE AIR QUALITY PREDICTION REPORT', margin + 6, currentY + 8.5)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(148, 163, 184) // slate-400
  doc.text('CPCB Standard Assessment • Surface Machine Learning Prediction Model', margin + 6, currentY + 15)

  currentY += 24

  // -------------------------------------------------------------------------
  // 1. Executive Summary & AQI Highlights
  // -------------------------------------------------------------------------
  const summaryBoxHeight = 30
  doc.setFillColor(248, 250, 252) // slate-50
  doc.setDrawColor(226, 232, 240) // slate-200
  doc.roundedRect(margin, currentY, contentWidth, summaryBoxHeight, 2, 2, 'FD')

  // Overall AQI Value Block
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(71, 85, 105) // slate-600
  doc.text('OVERALL AQI', margin + 8, currentY + 9)

  doc.setFontSize(22)
  doc.setTextColor(15, 23, 42)
  doc.text(String(data.aqi.value), margin + 8, currentY + 22)

  // Category Badge
  const catTheme = CPCB_PDF_THEME[data.aqi.category] || { bg: [100, 116, 139], text: [255, 255, 255] }
  const catText = data.aqi.category.toUpperCase()
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8.5)
  const catTextWidth = doc.getTextWidth(catText)
  const badgeWidth = catTextWidth + 8
  const badgeX = margin + 38
  const badgeY = currentY + 13

  doc.setFillColor(catTheme.bg[0], catTheme.bg[1], catTheme.bg[2])
  doc.roundedRect(badgeX, badgeY, badgeWidth, 6.5, 1.5, 1.5, 'F')
  doc.setTextColor(catTheme.text[0], catTheme.text[1], catTheme.text[2])
  doc.text(catText, badgeX + 4, badgeY + 4.5)

  // Category descriptor note
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7.5)
  doc.setTextColor(100, 116, 139)
  doc.text('CPCB Sub-Index Maximum', margin + 38, currentY + 25)

  // Dominant Pollutant Box
  const domX = margin + contentWidth - 55
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(7.5)
  doc.setTextColor(100, 116, 139)
  doc.text('DOMINANT POLLUTANT', domX, currentY + 9)

  doc.setFontSize(13)
  doc.setTextColor(217, 119, 6) // amber-600
  doc.text(data.dominant_pollutant || 'N/A', domX, currentY + 19)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7)
  doc.setTextColor(148, 163, 184)
  doc.text('Highest contributing factor', domX, currentY + 25)

  currentY += summaryBoxHeight + 5

  // -------------------------------------------------------------------------
  // 2. Location and Prediction Information
  // -------------------------------------------------------------------------
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(10)
  doc.setTextColor(15, 23, 42)
  doc.text('Location & Timeline Information', margin, currentY)
  currentY += 3

  const nowFormatted = new Date().toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'medium',
  })

  const locDisplay = locationName && locationName.trim() ? locationName.trim() : 'Coordinates Selection'
  const latDisplay = `${Math.abs(data.location.latitude).toFixed(4)}° ${data.location.latitude >= 0 ? 'N' : 'S'}`
  const lonDisplay = `${Math.abs(data.location.longitude).toFixed(4)}° ${data.location.longitude >= 0 ? 'E' : 'W'}`

  autoTable(doc, {
    startY: currentY,
    margin: { left: margin, right: margin },
    theme: 'plain',
    styles: {
      fontSize: 8,
      cellPadding: 1.5,
      textColor: [51, 65, 85],
    },
    columnStyles: {
      0: { fontStyle: 'bold', textColor: [71, 85, 105], cellWidth: 40 },
      1: { cellWidth: 55 },
      2: { fontStyle: 'bold', textColor: [71, 85, 105], cellWidth: 40 },
      3: { cellWidth: 51 },
    },
    body: [
      ['Location Name:', locDisplay, 'Target Prediction Date:', data.date],
      ['Coordinates:', `${latDisplay}, ${lonDisplay}`, 'Report Generated:', nowFormatted],
    ],
  })

  // @ts-expect-error - jspdf-autotable extends jsPDF instance
  currentY = doc.lastAutoTable.finalY + 4

  // -------------------------------------------------------------------------
  // 3. Pollutant-Wise Prediction Results
  // -------------------------------------------------------------------------
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(10)
  doc.setTextColor(15, 23, 42)
  doc.text('Pollutant-Wise Prediction Results', margin, currentY)
  currentY += 3

  const tableBody = POLLUTANTS_ORDER.map((pollutant) => {
    const rawVal = data.predictions[pollutant]
    const conc = typeof rawVal === 'number' && !isNaN(rawVal) ? rawVal.toFixed(1) : 'Unavailable'
    const unit = POLLUTANT_UNITS[pollutant] || 'ug/m3'
    const subIdxVal = data.sub_indices[pollutant]
    const subIndex = typeof subIdxVal === 'number' && !isNaN(subIdxVal) ? String(subIdxVal) : 'Unavailable'

    return [pollutant, conc, unit, subIndex]
  })

  autoTable(doc, {
    startY: currentY,
    margin: { left: margin, right: margin },
    head: [['Pollutant', 'Predicted Concentration', 'Unit', 'AQI Sub-index']],
    body: tableBody,
    theme: 'grid',
    headStyles: {
      fillColor: [30, 41, 59], // slate-800
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      fontSize: 8.5,
      halign: 'left',
    },
    columnStyles: {
      0: { cellWidth: 40, fontStyle: 'bold' },
      1: { cellWidth: 55, halign: 'right' },
      2: { cellWidth: 40, halign: 'center' },
      3: { cellWidth: 51, halign: 'right', fontStyle: 'bold' },
    },
    styles: {
      fontSize: 8,
      cellPadding: 2,
      lineColor: [226, 232, 240],
      lineWidth: 0.1,
    },
    alternateRowStyles: {
      fillColor: [248, 250, 252],
    },
  })

  // @ts-expect-error - jspdf-autotable extends jsPDF instance
  currentY = doc.lastAutoTable.finalY + 4

  // -------------------------------------------------------------------------
  // 4. Data Quality and Reliability Information
  // -------------------------------------------------------------------------
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(10)
  doc.setTextColor(15, 23, 42)
  doc.text('Data Quality & Provenance', margin, currentY)
  currentY += 3

  // Filter satellite provenance to avoid leaking internal features/VWS
  const satProvEntries = Object.entries(data.satellite_provenance || {}).filter(
    ([key]) => key !== 'VWS' && key !== 'Synthetic VWS'
  )

  const qualityColor: [number, number, number] =
    data.data_quality === 'HIGH'
      ? [16, 185, 129] // emerald-500
      : data.data_quality === 'MODERATE'
        ? [245, 158, 11] // amber-500
        : [239, 68, 68] // rose-500

  // Data Quality Level Banner
  doc.setFillColor(248, 250, 252)
  doc.setDrawColor(226, 232, 240)
  doc.roundedRect(margin, currentY, contentWidth, 10, 1.5, 1.5, 'FD')

  doc.setFillColor(qualityColor[0], qualityColor[1], qualityColor[2])
  doc.circle(margin + 5, currentY + 5, 2, 'F')

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(15, 23, 42)
  doc.text(`Quality Classification: ${data.data_quality}`, margin + 10, currentY + 6.5)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7.5)
  doc.setTextColor(100, 116, 139)
  const qualityDesc =
    data.data_quality === 'HIGH'
      ? 'All required inputs available.'
      : data.data_quality === 'MODERATE'
        ? 'Inputs available.'
        : 'Satellite observations unavailable; fallback estimation applied.'
  doc.text(qualityDesc, margin + 65, currentY + 6.5)

  currentY += 13

  // Satellite Provenance Breakdown Table
  if (satProvEntries.length > 0) {
    const provRows = satProvEntries.map(([key, prov]) => {
      const isAvailable = prov && (prov.value !== null && prov.value !== undefined || Boolean(prov.source))
      const statusDesc = isAvailable ? 'Available' : 'Unavailable'
      return [key, statusDesc]
    })

    autoTable(doc, {
      startY: currentY,
      margin: { left: margin, right: margin },
      head: [['Environmental Variable', 'Status']],
      body: provRows,
      theme: 'grid',
      headStyles: {
        fillColor: [71, 85, 105],
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 7.5,
      },
      styles: {
        fontSize: 7,
        cellPadding: 1.5,
        lineColor: [226, 232, 240],
        lineWidth: 0.1,
      },
      columnStyles: {
        0: { cellWidth: 45, fontStyle: 'bold' },
        1: { cellWidth: 141 },
      },
    })

    // @ts-expect-error - jspdf-autotable extends jsPDF instance
    currentY = doc.lastAutoTable.finalY + 4
  }

  // Extreme underestimation warning callout if applicable
  const hasSpatialReconstruction = ['AOD', 'NO2'].some(
    (k) => data.satellite_provenance?.[k]?.source === 'spatiotemporal_gapfill'
  )
  if (data.data_quality === 'LIMITED' && hasSpatialReconstruction) {
    const alertBoxHeight = 10
    doc.setFillColor(254, 242, 242) // rose-50
    doc.setDrawColor(254, 202, 202) // rose-200
    doc.roundedRect(margin, currentY, contentWidth, alertBoxHeight, 1.5, 1.5, 'FD')

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(7.5)
    doc.setTextColor(185, 28, 28) // rose-700
    doc.text(
      'Warning: Limited data quality. Spatial reconstruction may underestimate localized pollution extremes.',
      margin + 4,
      currentY + 6.5
    )
    currentY += alertBoxHeight + 4
  }

  // -------------------------------------------------------------------------
  // 5. Methodology Note & Scientific Disclaimer
  // -------------------------------------------------------------------------
  if (currentY > pageHeight - 32) {
    doc.addPage()
    currentY = margin
  }

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8.5)
  doc.setTextColor(15, 23, 42)
  doc.text('Methodology & Advisory Note', margin, currentY)
  currentY += 3.5

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7)
  doc.setTextColor(100, 116, 139)
  const methodologyText =
    'The system estimates concentrations of six air pollutants using a machine-learning model. These predicted concentrations are converted into pollutant-specific sub-indices using CPCB breakpoint calculations. The overall AQI is determined by the maximum pollutant sub-index.'
  const disclaimerText =
    'Note: These estimates are generated from satellite observations, reanalysis models, and surface machine-learning regression. They are model-based estimates and are not direct ground-station measurements.'

  const splitMethodology = doc.splitTextToSize(methodologyText, contentWidth)
  doc.text(splitMethodology, margin, currentY)
  currentY += splitMethodology.length * 3.2 + 1.5

  const splitDisclaimer = doc.splitTextToSize(disclaimerText, contentWidth)
  doc.text(splitDisclaimer, margin, currentY)

  // -------------------------------------------------------------------------
  // Header and Footer for all pages
  // -------------------------------------------------------------------------
  const totalPages = doc.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)

    // Footer rule
    doc.setDrawColor(226, 232, 240)
    doc.setLineWidth(0.3)
    doc.line(margin, pageHeight - 12, pageWidth - margin, pageHeight - 12)

    // Footer text
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7.5)
    doc.setTextColor(148, 163, 184)
    doc.text('SURFACE AIR QUALITY PREDICTION REPORT', margin, pageHeight - 8)
    doc.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - 8, { align: 'right' })
  }

  // -------------------------------------------------------------------------
  // Construct Descriptive Sanitised Filename & Save
  // -------------------------------------------------------------------------
  let locSlug = 'Location'
  if (locationName && locationName.trim()) {
    // Take the main part before comma if it's an address, or whole name
    const primaryName = locationName.split(',')[0].trim()
    locSlug = sanitizeFilename(primaryName)
  } else {
    const latStr = `${Math.abs(data.location.latitude).toFixed(3)}${data.location.latitude >= 0 ? 'N' : 'S'}`
    const lonStr = `${Math.abs(data.location.longitude).toFixed(3)}${data.location.longitude >= 0 ? 'E' : 'W'}`
    locSlug = `${latStr}_${lonStr}`
  }

  const dateSlug = sanitizeFilename(data.date || new Date().toISOString().slice(0, 10))
  const filename = `Surface_AQI_Report_${locSlug}_${dateSlug}.pdf`

  doc.save(filename)
}
