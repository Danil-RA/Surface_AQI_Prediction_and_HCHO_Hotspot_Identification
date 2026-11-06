# Contributing Guidelines

Thank you for your interest in contributing to the **Surface Air Quality Prediction and HCHO Hotspot Identification** project. We welcome research contributions, bug fixes, feature enhancements, and documentation improvements.

---

## 1. Code of Conduct & Research Standards
- Strive for scientific integrity: ensure empirical claims, metrics, and data sources are properly validated and attributed.
- Maintain respectful, constructive communication across all issues, pull requests, and discussions.

---

## 2. Development Setup

### 2.1 Backend Environment
1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/Danil-RA/Surface_AQI_Prediction_and_HCHO_Hotspot_Identification.git
   cd Surface_AQI_Prediction_and_HCHO_Hotspot_Identification
   ```
2. Initialize and activate a Python virtual environment:
   ```bash
   cd api
   python -m venv .venv
   source .venv/bin/activate       # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run backend tests:
   ```bash
   pytest aqi/test_breakpoints.py -v
   ```

### 2.2 Frontend Environment
1. Navigate to the `web/` directory:
   ```bash
   cd ../web
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Verify TypeScript compilation and production build:
   ```bash
   npm run typecheck
   npm run build
   ```

---

## 3. Contribution Workflow

1. **Branching Strategy**:
   - Create a feature or bugfix branch branched from `master`:
     ```bash
     git checkout -b feature/your-feature-name
     ```
2. **Commit Guidelines**:
   - Write clear, concise commit messages adhering to standard conventions (e.g., `feat:`, `fix:`, `docs:`, `refactor:`).
   - Keep commits focused and atomic.
3. **Repository Hygiene**:
   - Never commit sensitive files, credentials, private API keys, or `.env` files.
   - Do not stage local Python virtual environments (`.venv/`, `gapfill_venv/`) or Node build artifacts (`dist/`, `node_modules/`).
   - Use Git LFS for binary machine-learning artifacts (`.pkl`, `.parquet`).
4. **Pull Requests**:
   - Ensure all automated unit tests and type checks pass cleanly before submitting.
   - Provide a clear PR description summarizing the changes and testing performed.

---

## 4. Coding Standards

- **Python**: Follow PEP 8 guidelines. Type hints are encouraged for API schemas and service functions.
- **TypeScript / React**: Use functional components with hooks, strict typing, and avoid `any` where possible.
- **Geospatial & AQI Conventions**:
  - Adhere strictly to CPCB breakpoint tables (`api/aqi/breakpoints.py`).
  - Do not implement floating-point breakpoint calculations in the frontend.
  - Coordinate order: standard `[longitude, latitude]` for GeoJSON, and `(latitude, longitude)` for API endpoints.

