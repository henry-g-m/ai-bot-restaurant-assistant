terraform {
  backend "azurerm" {
    # These values are set via -backend-config flags in CI/CD
    # Local development: set these environment variables or use -backend-config flags
    # TF_VAR_backend_resource_group, TF_VAR_backend_storage_account, TF_VAR_backend_container, TF_VAR_backend_key
  }
}
