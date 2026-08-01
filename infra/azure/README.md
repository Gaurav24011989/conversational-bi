# Azure infrastructure (test deployment)

Bicep templates for the GitHub Actions **Deploy to Azure** pipeline.

## Layout

```
infra/azure/
├── main.bicep                 # Entry point
├── parameters/test.bicepparam # Example parameters (local CLI)
└── modules/
    ├── acr.bicep
    ├── postgres.bicep
    ├── redis.bicep
    ├── container-apps.bicep
    └── static-web-app.bicep
```

## Local validation

```bash
az bicep build --file infra/azure/main.bicep
```

## Local deploy (optional)

See [docs/runbooks/azure-deploy.md](../../docs/runbooks/azure-deploy.md) for prerequisites and secrets.

```bash
export POSTGRES_ADMIN_PASSWORD='...'
export SECRET_KEY='...'
export ENCRYPTION_KEY='...'
export GEMINI_API_KEY='...'

az group create --name rg-conversational-bi-test --location eastus

az deployment group create \
  --resource-group rg-conversational-bi-test \
  --template-file infra/azure/main.bicep \
  --parameters infra/azure/parameters/test.bicepparam
```
