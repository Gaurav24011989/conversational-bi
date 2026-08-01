# Azure deployment runbook

Deploy **Conversational BI** to Azure for end-to-end testing. The pipeline provisions managed infrastructure, builds container images, deploys the API and Celery worker to **Azure Container Apps**, and publishes the React SPA to **Azure Static Web Apps**.

For production hardening (private networking, Key Vault, autoscaling policies), extend this test setup later.

---

## Prerequisites

Complete these **once** before running the pipeline.

### Azure subscription

| Requirement | Details |
|-------------|---------|
| Subscription | Active Azure subscription with permission to create resource groups and deploy resources |
| Billing | Test stack costs roughly **$1.50–2.00/day** when left running (see architecture cost notes) |
| Region | Default `eastus`; any region that supports Container Apps, PostgreSQL Flexible Server, and Redis |

### Local tools (for one-time setup and troubleshooting)

| Tool | Purpose |
|------|---------|
| [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) `>= 2.60` | Create service principal, inspect resources |
| [GitHub CLI](https://cli.github.com/) (optional) | Manage repository secrets |
| `openssl` (optional) | Generate `SECRET_KEY` and `ENCRYPTION_KEY` |

### GitHub repository

| Requirement | Details |
|-------------|---------|
| Repository | This repo pushed to GitHub |
| Actions | GitHub Actions enabled |
| Branch | Deploy workflow runs on `main` (push) or manually via **workflow_dispatch** |

---

## Pipeline inputs

### GitHub Actions secrets (required)

Set these under **Settings → Secrets and variables → Actions → New repository secret**.

| Secret | Description | How to generate |
|--------|-------------|-----------------|
| `AZURE_CLIENT_ID` | App registration (service principal) client ID for OIDC login | See [One-time Azure OIDC setup](#one-time-azure-oidc-setup) |
| `AZURE_TENANT_ID` | Microsoft Entra tenant ID | `az account show --query tenantId -o tsv` |
| `AZURE_SUBSCRIPTION_ID` | Target subscription ID | `az account show --query id -o tsv` |
| `POSTGRES_ADMIN_PASSWORD` | PostgreSQL admin password (min 8 chars, mixed case + numbers) | `openssl rand -base64 24` |
| `SECRET_KEY` | JWT signing secret | `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | Fernet key for datasource credentials (32+ chars) | `openssl rand -base64 32` |
| `GEMINI_API_KEY` | Google Gemini API key | [Google AI Studio](https://aistudio.google.com/apikey) |

### Workflow dispatch inputs (optional — manual runs only)

Trigger via **Actions → Deploy to Azure → Run workflow**.

| Input | Default | Description |
|-------|---------|-------------|
| `environment_name` | `test` | Suffix for resource names (e.g. `cbi-test-api`, `rg-conversational-bi-test`) |
| `azure_location` | `eastus` | Azure region |
| `deploy_infrastructure` | `true` | Run Bicep to create/update Azure resources |
| `deploy_frontend` | `true` | Build and deploy React app to Static Web Apps |

### Automatic triggers

| Event | Behavior |
|-------|----------|
| Push to `main` | Runs full deploy when `backend/`, `frontend/`, `infra/`, or the deploy workflow changes |
| Pull request | Runs **CI** workflow only (tests + build); no Azure deploy |

---

## One-time Azure OIDC setup

Create a federated identity so GitHub Actions can deploy without storing Azure passwords.

```bash
# Variables — change for your environment
SUBSCRIPTION_ID="<your-subscription-id>"
RESOURCE_GROUP="rg-conversational-bi-test"
LOCATION="eastus"
APP_NAME="github-cbi-deploy"
GITHUB_ORG_OR_USER="<github-org-or-username>"
GITHUB_REPO="conversational-bi"   # repository name

az login
az account set --subscription "$SUBSCRIPTION_ID"

# Create resource group (pipeline also creates it; safe to run early)
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

# App registration
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
SP_OBJECT_ID=$(az ad sp create --id "$APP_ID" --query id -o tsv)

# Federated credential for main branch
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters "{
    \"name\": \"github-main\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:${GITHUB_ORG_OR_USER}/${GITHUB_REPO}:ref:refs/heads/main\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

# Federated credential for manual workflow_dispatch from any branch
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters "{
    \"name\": \"github-workflow\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:${GITHUB_ORG_OR_USER}/${GITHUB_REPO}:environment:azure-test\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

# Grant Contributor on the resource group
az role assignment create \
  --assignee "$APP_ID" \
  --role Contributor \
  --scope "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"

echo "AZURE_CLIENT_ID=$APP_ID"
echo "AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)"
echo "AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID"
```

Add the three `AZURE_*` values as GitHub secrets. For `workflow_dispatch` from non-`main` branches, create a GitHub Environment named `azure-test` and add the second federated credential subject, or add a credential for your branch.

---

## What the pipeline deploys

```
┌─────────────────────┐     ┌──────────────────────────┐
│ Azure Static Web    │────▶│ Container App: API       │
│ Apps (React SPA)    │     │ (FastAPI + migrations)   │
└─────────────────────┘     └───────────┬──────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
         ┌──────────────────┐  ┌─────────────────┐  ┌─────────────────┐
         │ PostgreSQL       │  │ Redis Cache     │  │ Container App:  │
         │ Flexible B1ms    │  │ Basic C0        │  │ Celery worker   │
         └──────────────────┘  └─────────────────┘  └─────────────────┘
                                          ▲
                              ┌───────────┴───────────┐
                              │ Azure Container       │
                              │ Registry (Basic)      │
                              └───────────────────────┘
```

| Component | Azure resource | Bicep module |
|-----------|----------------|--------------|
| API | Container App `cbi-{env}-api` | `modules/container-apps.bicep` |
| Worker | Container App `cbi-{env}-worker` | `modules/container-apps.bicep` |
| Database | PostgreSQL Flexible Server `cbi-{env}-pg` | `modules/postgres.bicep` |
| Cache / queue | Redis `cbi-{env}-redis` | `modules/redis.bicep` |
| Images | ACR `cbi{env}acr` | `modules/acr.bicep` |
| Frontend | Static Web App `cbi-{env}-web` | `modules/static-web-app.bicep` |

Infrastructure definition: `infra/azure/main.bicep`

---

## Run the deployment

### Option A — Manual (recommended for first deploy)

1. Complete [Prerequisites](#prerequisites) and [One-time Azure OIDC setup](#one-time-azure-oidc-setup).
2. Add all [GitHub Actions secrets](#github-actions-secrets-required).
3. Open **Actions → Deploy to Azure → Run workflow**.
4. Leave defaults (`environment_name=test`, `deploy_infrastructure=true`, `deploy_frontend=true`).
5. Wait for all jobs: **Validate → Infrastructure → Build and push → Deploy Container Apps → Deploy frontend → Summary**.
6. Open the **Deployment summary** job for API URL.

### Option B — Push to main

Merge to `main` with changes under `backend/`, `frontend/`, or `infra/`. The deploy workflow runs automatically after CI-related paths change.

---

## Verify the deployment

```bash
RESOURCE_GROUP="rg-conversational-bi-test"
ENV="test"

# API health
API_URL=$(az containerapp show \
  --name "cbi-${ENV}-api" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)
curl -fsS "https://${API_URL}/health"

# Frontend URL
az staticwebapp show \
  --name "cbi-${ENV}-web" \
  --resource-group "$RESOURCE_GROUP" \
  --query "defaultHostname" -o tsv
```

### Application smoke test

1. Open the Static Web App URL in a browser.
2. Register a new organization/user.
3. Create a project and register a datasource.
4. Refresh schema, start a conversation, and send a natural-language query.

API interactive docs: `https://<api-fqdn>/docs`

---

## Pipeline jobs reference

| Job | Purpose |
|-----|---------|
| `validate` | Backend ruff + pytest; frontend build |
| `infrastructure` | Create resource group; deploy Bicep |
| `build-and-push` | Build `backend/docker/Dockerfile`; push to ACR |
| `deploy-apps` | Update API and worker revisions; wait for `/health` |
| `deploy-frontend` | Build SPA with `VITE_API_BASE_URL=<api-url>`; upload to SWA |
| `summary` | Write deployment URLs to the GitHub Actions summary |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `AADSTS700213` / login failure | OIDC federated credential mismatch | Verify `subject` matches `repo:ORG/REPO:ref:refs/heads/main` |
| Container App revision unhealthy | DB not reachable or migrations failed | Check API logs: `az containerapp logs show -n cbi-test-api -g rg-conversational-bi-test` |
| `Image pull failed` | ACR role not propagated yet | Re-run workflow after 2–3 minutes |
| Frontend calls wrong API | Stale `VITE_API_BASE_URL` | Re-run deploy with `deploy_frontend=true` |
| Redis connection errors | SSL URL required | Bicep sets `rediss://` on port 6380 automatically |
| PostgreSQL connection timeout | Firewall | Bicep opens Azure services + all IPs for **test only** |

### View logs

```bash
az containerapp logs show \
  --name cbi-test-api \
  --resource-group rg-conversational-bi-test \
  --follow

az containerapp logs show \
  --name cbi-test-worker \
  --resource-group rg-conversational-bi-test \
  --follow
```

### Re-deploy application only (skip infrastructure)

Run workflow with `deploy_infrastructure=false`. Image build, Container App update, and frontend deploy still run.

---

## Security notes (test environment)

- PostgreSQL firewall includes `0.0.0.0–255.255.255.255` for simplicity. **Remove before production.**
- Secrets are passed to Container Apps via Bicep secure parameters. For production, use **Azure Key Vault** references.
- CORS is `allow_origins=["*"]` in the API. Restrict to your frontend domain in production.

---

## Related docs

- [Azure teardown runbook](./azure-teardown.md)
- [Architecture](../../docs/architecture.md)
- [Backend env reference](../../backend/.env.example)
- [Frontend env reference](../../frontend/.env.example)
