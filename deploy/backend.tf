terraform {
  backend "azurerm" {
    resource_group_name  = "rg-chat-bot"
    storage_account_name = "tfrstate"
    container_name       = "tfstate"
    key                  = "dev.tfstate"
  }
}
