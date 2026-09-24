# Phase 2 Azure Deployment Runbook

Deploy Phase 2 (multi-restaurant, document segregation, admin panel) to Azure.

## Prerequisites
- Azure CLI installed and authenticated: `az login`
- Subscription: (verify with `az account show`)
- Resource Group: `rg-chat-bot` (should exist from Phase 1)
- Key Vault: `restaurant-bot-kv` with admin password secret
- Cosmos DB: `restaurant_bot` database with `documents` container (updated indexing policy)

## Pre-Deployment Checklist
- [ ] All tests pass locally: `uv run pytest tests/ -q`
- [ ] Manual testing complete: See `PHASE2-TESTING.md`
- [ ] Git branch clean (all changes committed): `git status`
- [ ] requirements.txt updated: `uv export --no-dev --format requirements-txt > requirements.txt`
- [ ] Environment variables verified on App Service

## Step 1: Update Cosmos DB Vector Index Policy

Apply the updated indexing policy to support `restaurant_id` filtering in vector queries.

```bash
# (Optional) Create index policy file if not using defaults
# See deploy/azure/cosmos-setup-phase2.txt for policy details

# Update the documents container
az cosmosdb sql container update \
  --account-name <cosmos-account-name> \
  --database-name restaurant_bot \
  --name documents \
  --resource-group rg-chat-bot \
  --idx '{"indexingPolicy": {"indexingMode": "consistent", "includedPaths": [{"path": "/*"}], "excludedPaths": [{"path": "/\"_etag\"/?" }], "vectorIndexes": [{"path": "/embedding", "kind": "hnsw", "m": 4, "efConstruction": 400, "efSearch": 40}]}}'

# Verify update
az cosmosdb sql container show \
  --account-name <cosmos-account-name> \
  --database-name restaurant_bot \
  --name documents \
  --resource-group rg-chat-bot \
  --query "resource.indexingPolicy.vectorIndexes"
```

## Step 2: Update Key Vault Secrets

Ensure the admin password is stored in Key Vault (required for admin panel).

```bash
# Check if admin password exists
az keyvault secret list \
  --vault-name restaurant-bot-kv \
  --query "[].name" -o tsv | grep admin-upload-password

# If not present, add it
az keyvault secret set \
  --vault-name restaurant-bot-kv \
  --name admin-upload-password \
  --value "your-secure-password-here"
```

## Step 3: Export Dependencies

Update requirements.txt with pinned dependencies for Azure Oryx builder.

```bash
# From repo root
uv export --no-dev --format requirements-txt > requirements.txt

# Verify it includes python-multipart (needed for file uploads)
grep python-multipart requirements.txt
```

## Step 4: Deploy to Azure App Service

```bash
# 1. Export pinned deps for Azure Oryx
uv export --no-dev --format requirements-txt > requirements.txt

# 2. Deploy the App Service (code will be pulled from git/zip)
az webapp up \
  --runtime "PYTHON:3.12" \
  --sku F1 \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot \
  --location eastus2

# 3. Set the startup command (FastAPI doesn't auto-detect)
az webapp config set \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot \
  --startup-file "uvicorn restaurant_bot.main:app --host 0.0.0.0 --port 8000"

# 4. Ensure managed identity is enabled (for Key Vault access)
az webapp identity assign \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot

# 5. Grant "Key Vault Secrets User" role to the app's managed identity
PRINCIPAL_ID=$(az webapp identity show \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot \
  --query principalId -o tsv)

az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee $PRINCIPAL_ID \
  --scope $(az keyvault show \
    --name restaurant-bot-kv \
    --query id -o tsv)

# 6. Set environment variables on App Service
az webapp config appsettings set \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot \
  --settings \
    KEY_VAULT_URL="https://restaurant-bot-kv.vault.azure.net/" \
    AZURE_CLIENT_ID="<managed-identity-client-id>" \
    AZURE_TENANT_ID="<azure-tenant-id>"

# 7. (Optional) If firewall was locked from Phase 1, keep it open for F1 SKU
# (See Phase 1 deployment notes for tradeoff explanation)
```

## Step 5: Smoke Test

```bash
# 1. Get the deployed URL
DEPLOYED_URL="https://chat-bot-restaurant-egm.azurewebsites.net"

# 2. Test customer chat
curl $DEPLOYED_URL/
# Should load HTML

# 3. Test admin panel
curl $DEPLOYED_URL/admin.html
# Should load admin HTML

# 4. Test API endpoints
curl $DEPLOYED_URL/admin/status
# Should return {"active_restaurant": "chinese", "menu_items_count": 10}

# 5. Test chat
curl -X POST $DEPLOYED_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "show menu"}'
# Should return chat response

# 6. Manual testing in browser
# - Navigate to https://chat-bot-restaurant-egm.azurewebsites.net/
# - Test chat, menu, admin panel
# - Verify both Chinese and Mexican restaurants work
# - Upload test document via admin panel
```

## Step 6: Monitoring

```bash
# Check application logs
az webapp log tail \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot

# Check app insights (if enabled)
az monitor app-insights component show \
  --app chat-bot-restaurant-egm \
  --resource-group rg-chat-bot

# Restart app if needed
az webapp restart \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot
```

## Rollback Plan

If deployment fails:

```bash
# 1. Check logs for errors
az webapp log tail --name chat-bot-restaurant-egm --resource-group rg-chat-bot

# 2. Revert startup command to previous version
az webapp config set \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot \
  --startup-file "uvicorn restaurant_bot.main:app --host 0.0.0.0 --port 8000"

# 3. Restart the app
az webapp restart \
  --name chat-bot-restaurant-egm \
  --resource-group rg-chat-bot

# 4. Redeploy from previous commit if needed
git checkout <previous-commit-hash>
az webapp up --resource-group rg-chat-bot
```

## Post-Deployment Verification

- [ ] Chat loads and responds
- [ ] Both Chinese and Mexican restaurants accessible
- [ ] Admin panel authenticates with password
- [ ] Document upload works with correct restaurant_id
- [ ] Menu differs between restaurants
- [ ] Bot personality reflects restaurant
- [ ] No errors in application logs
- [ ] Response times acceptable (< 5 seconds cold start, < 2 seconds warm)

## Known Limitations

- **Cold Start Time**: First chat message loads ~1.6GB `bart-large-mnli` model, takes 5-10 seconds. Subsequent requests are < 2 seconds.
- **F1 SKU Limitations**: Cannot use VNet integration; firewall remains open (mitigated by API key requirement).
- **Session State**: In-memory cart resets on app restart; use database for persistent cart if needed.

## Support Contact

For issues or questions:
1. Check application logs: `az webapp log tail ...`
2. Verify Key Vault secrets are present
3. Confirm Cosmos DB connectivity
4. Review Phase 2 design rationale in PLAN.md
