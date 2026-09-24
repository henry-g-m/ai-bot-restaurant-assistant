variable "subscription_id" {
  type        = string
  description = "Azure subscription ID"
}

variable "app_name" {
  type        = string
  default     = "ai-bot-restaurant"
  description = "Name of the application"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment name (dev, staging, prod)"
}

variable "location" {
  type        = string
  default     = "eastus"
  description = "Azure region for resources"
}

variable "key_vault_id" {
  type        = string
  description = "Resource ID of the existing Key Vault"
}

variable "key_vault_url" {
  type        = string
  description = "URL of the existing Key Vault"
}

variable "menu_path" {
  type        = string
  default     = "/app/data/menu.yaml"
  description = "Path to the menu file"
}

variable "container_cpu" {
  type        = string
  default     = "0.5"
  description = "CPU allocation for the container (in cores)"
}

variable "container_memory" {
  type        = string
  default     = "1.0Gi"
  description = "Memory allocation for the container"
}

variable "min_replicas" {
  type        = number
  default     = 1
  description = "Minimum number of replicas"
}

variable "max_replicas" {
  type        = number
  default     = 3
  description = "Maximum number of replicas"
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Docker image tag"
}

variable "container_app_subnet_id" {
  type        = string
  default     = ""
  description = "Optional subnet ID for Container Apps infrastructure (leave empty for public)"
}
