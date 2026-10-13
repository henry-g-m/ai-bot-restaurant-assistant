terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
  subscription_id = var.subscription_id
}

# Data source for current context
data "azurerm_client_config" "current" {}

# Resource group
resource "azurerm_resource_group" "main" {
  name     = "${var.app_name}-${var.environment}-rg"
  location = var.location
}

# Container Registry
resource "azurerm_container_registry" "acr" {
  name                = replace("${var.app_name}${var.environment}acr", "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
}

# Log Analytics Workspace for Container Apps
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.app_name}-${var.environment}-law"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# Container Apps Environment (public - not using VNet integration)
resource "azurerm_container_app_environment" "main" {
  name                       = "${var.app_name}-${var.environment}-env"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
}

# Managed Identity for the Container App
resource "azurerm_user_assigned_identity" "main" {
  name                = "${var.app_name}-${var.environment}-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

# Role assignment for ACR pull
resource "azurerm_role_assignment" "acr_pull" {
  scope              = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id       = azurerm_user_assigned_identity.main.principal_id
}

# Key Vault read access for the managed identity (the vault uses RBAC authorization)
resource "azurerm_role_assignment" "kv_secrets_user" {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Container App
resource "azurerm_container_app" "main" {
  name                         = "${var.app_name}-${var.environment}-app"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.main.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.main.id
  }

  template {
    container {
      name   = var.app_name
      image  = "${azurerm_container_registry.acr.login_server}/${var.app_name}:${var.image_tag}"
      cpu    = var.container_cpu
      memory = var.container_memory

      env {
        name  = "PORT"
        value = "8000"
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "KEY_VAULT_URL"
        value = var.key_vault_url
      }

      env {
        name  = "MENU_PATH"
        value = var.menu_path
      }

      env {
        name  = "AZURE_TENANT_ID"
        value = data.azurerm_client_config.current.tenant_id
      }

      # Selects the user-assigned identity for DefaultAzureCredential (Key Vault access)
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.main.client_id
      }

    }

    min_replicas = var.min_replicas
    max_replicas = var.max_replicas
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 8000
    transport                  = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  depends_on = [
    azurerm_role_assignment.acr_pull,
    azurerm_role_assignment.kv_secrets_user
  ]
}

# Output the FQDN
output "container_app_fqdn" {
  value       = azurerm_container_app.main.latest_revision_fqdn
  description = "FQDN of the Container App"
}
