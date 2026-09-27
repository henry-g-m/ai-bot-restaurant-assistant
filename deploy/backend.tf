terraform {
  # Use local backend for development testing
  # After creating Azure Storage backend, change to:
  # backend "azurerm" {
  #   resource_group_name  = "your-rg"
  #   storage_account_name = "your-storage"
  #   container_name       = "tfstate"
  #   key                  = "prod.tfstate"
  # }
}
