# Migration from App Service to Container Apps

## What Changed

This project has been migrated from **Azure App Service** to **Azure Container Apps**, which provides:
- Better containerization support with Docker
- Modern container orchestration
- Automatic scaling based on HTTP traffic
- Cost-effective pricing model
- Environment-based configuration

## Old App Service Files

The following files from the old App Service deployment have been archived:
- `deploy/PHASE2-DEPLOY.md` — Old App Service runbook (use `DEPLOYMENT.md` instead)
- `deploy/PHASE2-TESTING.md` — Old App Service testing guide
- `deploy/azure/startup.txt` — Old gunicorn startup command
- `deploy/azure/cosmos-setup.txt` — Cosmos DB setup (still valid)
- `deploy/azure/keyvault-setup.txt` — Key Vault setup (still valid)

These files are kept for reference only. **Do not follow them for new deployments.**

## New Container App Files

- `Dockerfile` — Defines the container image (Python 3.12, FastAPI, uvicorn)
- `deploy/main.tf` — Terraform configuration for Container Apps, ACR, logging
- `deploy/variables.tf` — Terraform variables
- `deploy/backend.tf` — Terraform state backend configuration
- `deploy/terraform.tfvars.example` — Example configuration
- `.github/workflows/deploy.yml` — CI/CD pipeline (GitHub Actions)
- `DEPLOYMENT.md` — New deployment guide
- `.dockerignore` — Files to exclude from Docker build

## Key Differences

| Aspect | App Service | Container Apps |
|--------|-------------|-----------------|
| **Containerization** | Source code deployed directly | Docker image built and pushed to ACR |
| **Deployment** | `az webapp up` command | Terraform infrastructure-as-code |
| **CI/CD** | Manual or custom script | GitHub Actions workflow |
| **Scaling** | Manual SKU configuration | Automatic based on HTTP load |
| **Cost** | Fixed monthly cost | Per-request pricing (more cost-effective) |
| **Startup** | ~30-60 seconds (cold) | ~40-50 seconds (cold start, similar) |

## Secrets Management

Both deployments use the same Key Vault setup:
- **Key Vault Name**: Same as before
- **Secrets**: `admin-upload-password`, `cosmos-endpoint`, etc. (unchanged)
- **Authentication**: Managed identity (App Service) → Managed identity (Container App)

## Existing Resources

The following Azure resources remain the same:
- **Cosmos DB**: `restaurant_bot` database, `documents` container
- **Azure OpenAI**: Endpoint and deployment
- **Key Vault**: All secrets and access policies

## Deleting Old App Service

Once the Container App is running and verified, delete the old App Service:

```bash
# Delete the App Service
az webapp delete \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot

# (Optional) Delete the App Service Plan if not used by other apps
az appservice plan delete \
  --name chat-bot-restaurant-egm-plan \
  --resource-group rg-chat-bot
```

## First Deployment Steps

1. **Create Storage Account** for Terraform state (see `DEPLOYMENT.md`)
2. **Add GitHub Secrets** for CI/CD (see `DEPLOYMENT.md`)
3. **Create Service Principal** for Azure authentication (see `DEPLOYMENT.md`)
4. **Configure `terraform.tfvars`** with your Azure details
5. **Push to main branch** — GitHub Actions automatically builds and deploys
6. **Monitor deployment** in GitHub Actions and Azure Portal
7. **Delete old App Service** once verified

## Troubleshooting

If you encounter issues:
1. Check GitHub Actions workflow logs
2. Review Container App logs in Azure Portal
3. Verify managed identity has Key Vault access
4. Check Terraform state in the storage account

See `DEPLOYMENT.md` for detailed troubleshooting.
