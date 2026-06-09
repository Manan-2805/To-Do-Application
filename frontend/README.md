# TodoSphere Frontend Portal

This directory contains the source code for the interactive, responsive, and glassmorphic single-page React frontend application that powers the TodoSphere task management dashboard.

---

## Technical Stack

- **Framework**: [React](https://react.dev/) (v19)
- **Language**: TypeScript (strict mode compilation)
- **Build Tool**: [Vite](https://vite.dev/) (v8)
- **Styling**: Vanilla CSS Variables (supporting system-matched Light/Dark mode transitions)
- **Icons**: Lucide React
- **Router**: React Router DOM (v7)

---

## Directory Layout & Components

The frontend project is structured as follows:

```text
frontend/
├── src/
│   ├── main.tsx                  # React DOM Mounter
│   ├── App.tsx                   # Central router & session checker
│   ├── App.css                   # Global styles
│   ├── index.css                 # Main design tokens and responsive CSS stylesheet
│   ├── api/                      # Axios HTTP client requests (Auth, Tasks, Audits)
│   ├── components/               # Shareable components
│   │   ├── Header.tsx            # Global navigation navbar
│   │   ├── TaskChart.tsx         # Doughnut status allocation chart (SVG elements)
│   │   ├── TaskModal.tsx         # Consolidated Task CRUD modal
│   │   └── ThemeToggle.tsx       # System-preferred light/dark toggle switcher
│   └── pages/                    # Routed page layouts
│       ├── Login.tsx             # Auth login page
│       ├── SignUp.tsx            # New account signup registration
│       ├── Dashboard.tsx         # Metrics summary charts view
│       ├── Tasks.tsx             # Paginated task list table view
│       └── Audit.tsx             # DevOps IP/User-Agent logging audit trail view
└── tests/                        # Vitest components and Playwright E2E suites
```

---

## High-Quality Performance & Accessibility

TodoSphere Frontend is built with strict quality guidelines, achieving optimal browser compatibility and developer satisfaction:

1. **React Doctor Score: 96 / 100 ("Great")**
   - Implements O(1) key updates using stable identifiers in loops (avoiding array index keys).
   - Prevents stale `setState` reads in concurrent events using functional callback hooks (`prev => prev +/- 1`).
   - Uses `useRef` rather than state triggers to manage background values (e.g. upload files and search inputs).
   - Grouped related states to avoid bloated and inefficient re-renders.
2. **Accessible (A11y) Compliance**:
   - Semantic tags (e.g. using router `<Link>` wrappers rather than custom-div roles).
   - Screen-reader tags like `aria-label` applied on interactive control inputs (search inputs, toggle switches, close actions).
   - Clear input-label mappings (`htmlFor`) and font scaling safeguards (no text under 12px / 0.75rem).
3. **Lighthouse Score: 95+ (Performance, Accessibility, Best Practices, SEO)**
   - Minimal visual shifts.
   - Leverages system-level glassmorphic gradients and local storage to cache light/dark styles efficiently.

---

## Local Setup

### 1. Install Node Dependencies

Ensure you have [Node.js](https://nodejs.org/) installed (v18+ recommended):

```bash
npm install
```

### 2. Run the Development Server

Launch the local Hot-Module-Replacement (HMR) development server:

```bash
npm run dev
```

By default, the server runs at `http://localhost:5173`. Make sure the FastAPI backend is running on `http://localhost:8000`.

### 3. Build for Production

Generate the optimized static build directory in `dist/`:

```bash
npm run build
```

---

## Verification & Code Quality

Execute quality check targets locally:

### Code style and formatting (Prettier)

```bash
npm run format:check
npm run format
```

### Linter (ESLint)

```bash
npm run lint
```

### TypeScript Compile Check

```bash
npx tsc -b
```

### Vitest Unit Tests

Run local unit test cases:

```bash
npx vitest run
```

### Playwright E2E browser tests

Install headless chromium binaries and run local end-to-end tests:

```bash
npx playwright install chromium
npx playwright test
```

---

## Connection to the Main Ecosystem

This client application works in tandem with the FastAPI database services.

- Refer to the main [README.md](../README.md) for database container bindings and full-stack orchestration commands.
