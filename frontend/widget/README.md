# Conversational BI — React Widget

Embeddable React component for integrating natural-language data queries into any existing React application.

## Install

From the monorepo (local development):

```bash
cd frontend/widget
npm install
npm run build
```

In your host app, add the package via file path or published registry:

```bash
npm install conversational-bi-widget@file:../path/to/frontend/widget
```

Peer dependencies: `react` and `react-dom` (^18 or ^19).

## Quick start

```tsx
import { ConversationalBIWidget } from 'conversational-bi-widget'
import 'conversational-bi-widget/style.css'

function AnalyticsPanel() {
  const accessToken = '...' // JWT from your auth flow

  return (
    <ConversationalBIWidget
      apiBaseUrl="https://api.example.com"
      accessToken={accessToken}
      projectId="your-project-uuid"
      datasourceId="your-datasource-uuid"
      title="Sales insights"
      height={600}
      onError={(err) => console.error(err)}
      onConversationCreated={(conv) => console.log('Started', conv.id)}
    />
  )
}
```

## Props

| Prop | Required | Description |
|------|----------|-------------|
| `apiBaseUrl` | Yes | Backend origin (e.g. `https://api.example.com`) |
| `accessToken` | Yes | JWT from `POST /api/v1/auth/login` |
| `projectId` | Yes | Project UUID |
| `datasourceId` | Yes | Datasource UUID (used when creating a new conversation) |
| `conversationId` | No | Resume an existing conversation instead of creating one |
| `title` | No | Title for new conversations (default: "Ask your data") |
| `locale` | No | BCP-47 locale sent with message requests |
| `height` | No | Container height (default `560`) |
| `className` | No | Extra CSS class on the root element |
| `style` | No | Inline styles on the root element |
| `onError` | No | Error callback |
| `onConversationCreated` | No | Called when a new conversation is created |

## Advanced: compose with provider

For multiple widget instances or custom children that call the API:

```tsx
import {
  WidgetProvider,
  ConversationChat,
  createApiClient,
} from 'conversational-bi-widget'
import 'conversational-bi-widget/style.css'

function App() {
  return (
    <WidgetProvider apiBaseUrl="https://api.example.com" accessToken={token}>
      <ConversationChat
        projectId="..."
        datasourceId="..."
        conversationId="optional-existing-id"
      />
    </WidgetProvider>
  )
}

// Or use the API client directly:
const api = createApiClient('https://api.example.com')
const messages = await api.listMessages(token, conversationId)
```

## Styling

Styles are scoped under `.cbi-widget` to avoid conflicting with host app CSS. Import the bundled stylesheet:

```tsx
import 'conversational-bi-widget/style.css'
```

Override CSS variables on the root element for theming:

```css
.my-panel .cbi-widget {
  --cbi-color-primary: #7c3aed;
  --cbi-radius: 8px;
}
```

## Prerequisites

Before embedding the widget, ensure on the backend:

1. The user has a valid JWT with access to the project
2. The datasource is configured and schema has been refreshed
3. CORS allows requests from your host app's origin

## Build

```bash
npm run build
```

Outputs ESM/CJS bundles and TypeScript declarations in `dist/`.

## API workflow

1. Authenticate your user and obtain a JWT
2. Pass `projectId` and `datasourceId` to the widget
3. The widget creates a conversation (unless `conversationId` is provided)
4. Users send natural-language questions; responses render as tables and charts

See [backend/docs/api.md](../../backend/docs/api.md) for full API reference.
