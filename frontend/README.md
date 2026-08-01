# Conversational BI — Frontend

React + Vite single-page application for the Conversational BI platform. Connects to the FastAPI backend for auth, project management, datasource configuration, and natural-language data queries.

## Tech stack

| Layer | Technology |
|-------|------------|
| Framework | React 19 |
| Build | Vite 8 |
| Routing | React Router 7 |
| Charts | Recharts |
| E2E tests | Playwright |

## Quick start

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The dev server runs at http://localhost:5173 and proxies `/api` requests to the backend (default `http://localhost:8000`). Start the backend first:

```bash
cd backend
docker compose -f docker/docker-compose.yml up -d postgres redis
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend origin (empty string uses Vite proxy in dev) |

## Features

- **Auth**: Register, login, JWT session (localStorage), logout
- **Projects**: List and create projects for the user's organization
- **Data sources**: Add PostgreSQL, MySQL, MongoDB, or Elasticsearch connections; test and refresh schema
- **Conversations**: Start NL query sessions; render `QueryResponse` with tables, charts (bar, line, area, pie, scatter, metric), clarifications, and follow-up suggestions
- **Conversation history**: Stored client-side (backend has no list endpoint yet)

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm run test:e2e` | Run Playwright e2e tests |
| `npm run test:e2e:ui` | Playwright UI mode |

## React embed widget

The `widget/` package is a standalone library (`conversational-bi-widget`) for embedding the conversation UI in any React app.

```bash
cd frontend/widget
npm install
npm run build
```

Usage in a host app:

```tsx
import { ConversationalBIWidget } from 'conversational-bi-widget'
import 'conversational-bi-widget/style.css'

<ConversationalBIWidget
  apiBaseUrl="https://api.example.com"
  accessToken={jwt}
  projectId="..."
  datasourceId="..."
/>
```

See [widget/README.md](widget/README.md) for full props, theming, and advanced composition.

## E2E tests

Playwright tests mock the backend API via route interception — no live backend or LLM required.

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

Test suites:

| File | Coverage |
|------|----------|
| `e2e/auth.spec.ts` | Login, register, logout, redirects |
| `e2e/projects.spec.ts` | Project list, create, navigation, empty/error states |
| `e2e/datasources.spec.ts` | Datasource CRUD, test connection, schema refresh |
| `e2e/conversations.spec.ts` | Chat flow, query results, clarifications, errors |
| `e2e/edge-cases.spec.ts` | 401 handling, routing, empty states |

## Project structure

```
frontend/
  src/
    api/           # Typed API client
    components/    # Shared UI (charts, tables, layout)
    context/       # Auth provider
    utils/           # localStorage helpers
    pages/         # Route pages
    types/         # TypeScript API types
  widget/          # Embeddable React package (conversational-bi-widget)
  e2e/             # Playwright tests + API mocks
```
