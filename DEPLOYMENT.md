# Container App Deployment Guide

This project is deployed to Azure Container Apps instead of App Service, using Docker for containerization and Terraform for infrastructure-as-code.

## Overview

The deployment consists of:
1. **Docker Image**: Built and pushed to Azure Container Registry (ACR)
2. **Infrastructure**: Managed by Terraform (Container Apps, Load Analytics, ACR)
3. **CI/CD**: GitHub Actions automatically builds, pushes, and deploys on each push to main

## Prerequisites

### Local Development
- Docker Desktop or Docker CLI
- Terraform >= 1.0
- Azure CLI
- Python 3.12+

### Azure Setup
- Azure subscription with appropriate permissions
- Existing Key Vault (referenced by Container App for secrets)
- Azure Container Registry (created by Terraform)
- Storage account for Terraform state (one-time setup)

## One-Time Setup

### 1. Create Storage Account for Terraform State

```bash
# Set variables
export RG_NAME="your-resource-group"
export STORAGE_ACCOUNT="tfrstate$(date +%s%N | md5sum | head -c 8)"
export CONTAINER_NAME="tfstate"

# Create resource group
az group create --name $RG_NAME --location eastus

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RG_NAME \
  --location eastus \
  --sku Standard_LRS

# Create blob container
az storage container create \
  --name $CONTAINER_NAME \
  --account-name $STORAGE_ACCOUNT

# Get storage account key
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RG_NAME \
  --account-name $STORAGE_ACCOUNT \
  --query [0].value -o tsv)

echo "Storage Account: $STORAGE_ACCOUNT"
echo "Storage Key: $STORAGE_KEY"
```

Save these values — you'll need them for CI/CD secrets.

### 2. Set GitHub Secrets

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

```
AZURE_CLIENT_ID           # Service Principal client ID
AZURE_TENANT_ID           # Azure tenant ID
AZURE_SUBSCRIPTION_ID     # Azure subscription ID
REGISTRY_NAME             # ACR name (without .azurecr.io)
REGISTRY_USERNAME         # ACR admin username
REGISTRY_PASSWORD         # ACR admin password
TF_BACKEND_RG             # Resource group for Terraform state
TF_BACKEND_STORAGE        # Storage account for Terraform state
TF_BACKEND_CONTAINER      # Blob container for Terraform state (tfstate)
TF_BACKEND_KEY            # State file name (e.g., prod.tfstate)
```

### 3. Create Service Principal for GitHub Actions

```bash
# Create service principal
az ad sp create-for-rbac --name "github-actions-deployment" \
  --role "Contributor" \
  --scopes /subscriptions/$SUBSCRIPTION_ID

# Output will include:
# - clientId (AZURE_CLIENT_ID)
# - clientSecret (not needed, using OIDC instead in modern setup)
# - tenantId (AZURE_TENANT_ID)
```

## Local Deployment

### 1. Build Docker Image

```bash
# Build image
docker build -t ai-bot-restaurant:latest .

# Test locally
docker run -p 8000:8000 \
  -e KEY_VAULT_URL="https://your-keyvault.vault.azure.net/" \
  -e MENU_PATH="/app/data/menu.yaml" \
  ai-bot-restaurant:latest

# Visit http://localhost:8000
```

### 2. Deploy with Terraform

```bash
cd deploy

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan -out=tfplan

# Apply the changes
terraform apply tfplan
```

After deployment, get the Container App URL:

```bash
terraform output container_app_fqdn
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically:

1. **Build**: Creates a Docker image on every push to `main`
2. **Push**: Pushes image to Azure Container Registry
3. **Plan**: Runs `terraform plan` to show infrastructure changes
4. **Apply**: Applies Terraform changes to deploy/update the Container App

### Workflow Triggers

- Any push to `main` or `rag-intent-and-azure-deploy` branches
- Changes to source code, Dockerfile, or Terraform files
- Manual trigger via `workflow_dispatch`

## Environment Variables

The Container App is configured with:

| Variable | Source | Example |
|----------|--------|---------|
| PORT | Hardcoded | 8000 |
| ENVIRONMENT | From tfvars | dev/staging/prod |
| KEY_VAULT_URL | From tfvars | https://keyvault.vault.azure.net/ |
| MENU_PATH | From tfvars | /app/data/menu.yaml |
| AZURE_TENANT_ID | From Azure provider | xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx |

The application uses managed identity (AZURE_TENANT_ID) to authenticate with Key Vault. Additional secrets (admin-upload-password, etc.) are retrieved from Key Vault at runtime.

## Health Checks

The Container App has:
- **Liveness probe**: Checks `/docs` every 30 seconds (starts after 40s)
- **Readiness probe**: Checks `/docs` every 10 seconds (starts after 30s)

Both probes allow up to 3 consecutive failures before restarting.

## Scaling

Configure in `terraform.tfvars`:

```hcl
min_replicas = 1  # Always run at least 1 instance
max_replicas = 3  # Scale up to 3 instances under load
```

Container Apps automatically scales based on HTTP requests and CPU/memory usage.

## Monitoring

View logs in Azure Portal:
1. Go to your Container App resource
2. Navigate to **Monitoring** > **Log stream**
3. Or use Azure CLI: `az containerapp logs show --name <app-name> -g <resource-group>`

View metrics:
1. Go to your Container App resource
2. Navigate to **Monitoring** > **Metrics**
3. Select metrics like CPU, Memory, Request count, Response time

## Updating the Application

To deploy new code:

1. **Commit and push** your changes to `main`:
   ```bash
   git add .
   git commit -m "Update feature"
   git push origin main
   ```

2. **GitHub Actions** automatically:
   - Builds a new Docker image
   - Tags it with the commit SHA and branch name
   - Pushes it to ACR
   - Updates the Container App with the new image

3. **Monitor** the deployment:
   - Watch the GitHub Actions workflow in the **Actions** tab
   - Check the Container App logs in Azure Portal

## Rollback

If something goes wrong:

```bash
# View revision history
az containerapp revision list --name ai-bot-restaurant-dev-app \
  --resource-group ai-bot-restaurant-dev-rg

# Switch traffic to a previous revision
az containerapp revision set-traffic --name ai-bot-restaurant-dev-app \
  --resource-group ai-bot-restaurant-dev-rg \
  --traffic <previous-revision>=100
```

Or use Terraform to revert:

```bash
cd deploy
git revert <commit-hash>
git push
# GitHub Actions will automatically apply the changes
```

## Troubleshooting

### Container fails to start
- Check logs: `az containerapp logs show --name <app-name> -g <resource-group>`
- Verify environment variables: `az containerapp show --name <app-name> -g <resource-group>`
- Check Key Vault access: Ensure managed identity has `Get` and `List` permissions

### Terraform initialization fails
- Verify storage account exists and is accessible
- Check Azure CLI login: `az account show`
- Verify backend config in GitHub secrets

### Image pull fails
- Verify ACR credentials are correct
- Check ACR permissions for managed identity
- Ensure image exists in ACR: `az acr repository list --name <acr-name>`

## Clean Up

To delete all resources:

```bash
cd deploy
terraform destroy -var-file=terraform.tfvars
```

This removes:
- Container App
- Container App Environment
- Log Analytics Workspace
- Container Registry
- Resource Group

**WARNING**: This is irreversible. Ensure you have backups of important data.

## Cost Optimization

- **Min replicas**: Set to 0 for non-production environments (app will cold-start, ~40-50s)
- **Container size**: Start with 0.5 CPU, 1.0Gi memory; increase if needed
- **Log retention**: Currently set to 30 days; adjust in `deploy/main.tf`

## Support

For issues:
1. Check application logs in Azure Portal
2. Review GitHub Actions workflow logs
3. Run Terraform plan to identify issues: `cd deploy && terraform plan`
4. Check Azure documentation: https://learn.microsoft.com/azure/container-apps/
