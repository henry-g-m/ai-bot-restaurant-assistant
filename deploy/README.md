# Deployment Configuration

This directory contains the infrastructure-as-code and deployment scripts for the restaurant assistant bot.

## Files

### Terraform Configuration
- **`main.tf`** — Main Terraform configuration for Container Apps, ACR, and logging
- **`variables.tf`** — Variable definitions for Terraform
- **`backend.tf`** — Backend configuration for Terraform state (Azure Storage)
- **`terraform.tfvars.example`** — Example configuration file (copy to `terraform.tfvars`)

### Deployment Scripts
- **`DELETE_APP_SERVICE.sh`** — Bash script to delete the old App Service (Linux/macOS)
- **`DELETE_APP_SERVICE.ps1`** — PowerShell script to delete the old App Service (Windows)

### Documentation
- **`MIGRATION_NOTES.md`** — Notes about migrating from App Service to Container Apps
- **`../DEPLOYMENT.md`** — Comprehensive deployment guide (in project root)

### Legacy Files (Reference Only)
- **`azure/`** — Old Azure deployment notes (App Service specific)
  - `startup.txt` — Old gunicorn startup command
  - `cosmos-setup.txt` — Cosmos DB setup (still relevant)
  - `keyvault-setup.txt` — Key Vault setup (still relevant)
  - `one-time-setup/` — Vector index and indexing policy files
- **`PHASE2-DEPLOY.md`** — Old App Service deployment runbook (archived)
- **`PHASE2-TESTING.md`** — Old testing guide (archived)

## Deployment Workflow

### 1. First Time Setup
```bash
# Copy the example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your Azure details
code terraform.tfvars

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan -out=tfplan

# Apply the changes
terraform apply tfplan
```

### 2. Automated Deployments (via GitHub Actions)
- On every push to `main` branch
- On changes to source code, Dockerfile, or Terraform files
- Manual trigger via GitHub Actions UI

### 3. Clean Up Old Deployment

Once the Container App is running and verified:

**Linux/macOS:**
```bash
bash DELETE_APP_SERVICE.sh
```

**Windows:**
```powershell
.\DELETE_APP_SERVICE.ps1
```

Or manually with Azure CLI:
```bash
az webapp delete --name chat-bot-restaurant-egm --resource-group rg-chat-bot
```

## Key Resources Created

The Terraform configuration creates:

| Resource | Name | Purpose |
|----------|------|---------|
| Container App | `ai-bot-restaurant-{env}-app` | The main application |
| Container Registry | `aibotrestaurant{env}acr` | Stores Docker images |
| Container App Env | `ai-bot-restaurant-{env}-env` | Container orchestration |
| Managed Identity | `ai-bot-restaurant-{env}-identity` | Authentication for Key Vault/ACR |
| Log Analytics | `ai-bot-restaurant-{env}-law` | Monitoring and logs |
| Resource Group | `ai-bot-restaurant-{env}-rg` | Groups related resources |

## Environment Variables

The Container App is configured with these environment variables:

| Variable | Source | Example |
|----------|--------|---------|
| PORT | Hardcoded in container | 8000 |
| ENVIRONMENT | From `terraform.tfvars` | dev/staging/prod |
| KEY_VAULT_URL | From `terraform.tfvars` | https://keyvault.vault.azure.net/ |
| MENU_PATH | From `terraform.tfvars` | /app/data/menu.yaml |
| AZURE_TENANT_ID | From Azure provider | UUID |

Additional secrets are retrieved from Key Vault at runtime using managed identity.

## Troubleshooting

### Terraform Issues
```bash
# Check Terraform state
terraform state list

# Validate configuration
terraform validate

# See detailed error logs
export TF_LOG=DEBUG
terraform plan
```

### Container App Issues
```bash
# View Container App details
az containerapp show --name ai-bot-restaurant-dev-app \
  --resource-group ai-bot-restaurant-dev-rg

# View logs
az containerapp logs show --name ai-bot-restaurant-dev-app \
  --resource-group ai-bot-restaurant-dev-rg

# Check revisions
az containerapp revision list --name ai-bot-restaurant-dev-app \
  --resource-group ai-bot-restaurant-dev-rg
```

### Container Registry Issues
```bash
# List images in ACR
az acr repository list --name aibotrestaurantdevacr

# Check image tags
az acr repository show-tags --name aibotrestaurantdevacr \
  --repository ai-bot-restaurant
```

## Cost Optimization

1. **Set min_replicas to 0** for dev environments (auto-scales from zero)
2. **Reduce container resources** in non-production:
   - CPU: 0.25 (instead of 0.5)
   - Memory: 0.5Gi (instead of 1.0Gi)
3. **Adjust log retention** for non-prod (currently 30 days):
   - Edit in `main.tf`: `retention_in_days`

## Cost Estimation

### Container Apps Pricing
- **Per-request pricing**: ~$0.40 per million requests
- **Memory pricing**: ~$36/month per GB/month
- **vCPU pricing**: ~$144/month per vCPU/month

For the configured setup (1 instance, 0.5 CPU, 1GB memory):
- Baseline: ~$60-70/month (memory + CPU)
- Plus: ~$0.40 per million requests

### App Service Pricing (old)
- F1 (free): Limited, unreliable
- B1: ~$10-15/month
- S1: ~$50-70/month

## Support

For detailed information, see:
- `../DEPLOYMENT.md` — Comprehensive guide
- `MIGRATION_NOTES.md` — Migration details
- Azure Container Apps docs: https://learn.microsoft.com/azure/container-apps/
- Terraform Azure provider: https://registry.terraform.io/providers/hashicorp/azurerm/latest
