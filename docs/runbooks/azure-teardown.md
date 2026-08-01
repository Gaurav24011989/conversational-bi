# Azure teardown runbook

Remove the **Conversational BI** test deployment from Azure to stop ongoing charges.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Azure CLI | Logged in with permission to delete the resource group |
| Resource group name | Default: `rg-conversational-bi-test` (or your `environment_name` suffix) |

### Inputs

| Variable | Default | Description |
|----------|---------|-------------|
| `RESOURCE_GROUP` | `rg-conversational-bi-test` | Resource group created by the deploy pipeline |
| `ENVIRONMENT_NAME` | `test` | Environment suffix used during deploy |

---

## Delete all resources (recommended)

Deleting the resource group removes every resource deployed by Bicep: Container Apps, ACR, PostgreSQL, Redis, and Static Web Apps.

```bash
RESOURCE_GROUP="rg-conversational-bi-test"

az login
az group delete --name "$RESOURCE_GROUP" --yes --no-wait
```

Check deletion status:

```bash
az group exists --name "$RESOURCE_GROUP"
# false = deleted
```

---

## Optional: remove GitHub OIDC app registration

If you no longer need automated deploys:

```bash
APP_ID="<AZURE_CLIENT_ID from GitHub secrets>"
az ad app delete --id "$APP_ID"
```

Remove GitHub Actions secrets under **Settings → Secrets and variables → Actions**.

---

## Optional: delete federated credentials only

Keep the app registration but revoke GitHub access:

```bash
APP_ID="<AZURE_CLIENT_ID>"
az ad app federated-credential list --id "$APP_ID" -o table
az ad app federated-credential delete --id "$APP_ID" --federated-credential-id <credential-id>
```

---

## Verify no orphaned charges

```bash
az resource list --resource-group "$RESOURCE_GROUP" -o table
```

If the group is gone, no resources remain. ACR, PostgreSQL, and Redis are the main cost drivers — all are removed with the resource group.

---

## Related docs

- [Azure deployment runbook](./azure-deploy.md)
