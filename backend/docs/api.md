# API documentation for Conversational BI backend

See OpenAPI docs at `/docs` when the server is running.

## Authentication

All endpoints except `/auth/register`, `/auth/login`, and `/health` require a Bearer token.

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret","org_name":"Acme","org_slug":"acme"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}'
```

## Core workflow

1. Create a project
2. Register a data source
3. Test connection and refresh schema
4. Create a conversation
5. Send natural language messages

## Rate limits

- Per user: 60 requests/minute (configurable)
- Per organization: 1000 requests/minute (configurable)
