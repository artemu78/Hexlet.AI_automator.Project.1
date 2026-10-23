terraform {
  required_version = ">= 1.5"
  required_providers {
    yandex  = { source = "yandex-cloud/yandex", version = "~> 0.191" }
    archive = { source = "hashicorp/archive", version = "~> 2.7" }
    random  = { source = "hashicorp/random", version = "~> 3.7" }
  }
}
provider "yandex" {
  folder_id = var.folder_id
  cloud_id  = var.cloud_id
}
variable "folder_id" { type = string }
variable "cloud_id" { type = string }
variable "name" {
  type    = string
  default = "club-contact"
}
variable "allowed_origins" {
  type    = list(string)
  default = ["https://artemu78.github.io", "http://localhost:5173"]
}
resource "yandex_iam_service_account" "function" { name = "${var.name}-function" }
resource "yandex_iam_service_account" "gateway" { name = "${var.name}-gateway" }
resource "yandex_ydb_database_serverless" "contact" {
  name      = var.name
  folder_id = var.folder_id
}
resource "yandex_ydb_database_iam_binding" "writer" {
  database_id = yandex_ydb_database_serverless.contact.id
  role        = "ydb.editor"
  members     = ["serviceAccount:${yandex_iam_service_account.function.id}"]
}
resource "yandex_ydb_table" "submissions" {
  path              = "submissions"
  connection_string = yandex_ydb_database_serverless.contact.ydb_full_endpoint
  primary_key       = ["id"]
  dynamic "column" {
    for_each = { id = "Utf8", received_at = "Uint64", message = "Utf8", contacts = "Utf8" }
    content {
      name     = column.key
      type     = column.value
      not_null = column.key == "id"
    }
  }
  # Deliberately no TTL: accepted submissions are retained indefinitely.
}
resource "yandex_ydb_table" "rate_limits" {
  path              = "rate_limits"
  connection_string = yandex_ydb_database_serverless.contact.ydb_full_endpoint
  primary_key       = ["ip_key"]
  dynamic "column" {
    for_each = { ip_key = "Utf8", recent = "Utf8", updated_at = "Uint64" }
    content {
      name     = column.key
      type     = column.value
      not_null = column.key == "ip_key"
    }
  }
  ttl {
    column_name     = "updated_at"
    expire_interval = "PT10M"
    unit            = "seconds"
  }
}
resource "random_password" "ip_hash" {
  length  = 64
  special = false
}
data "archive_file" "function" {
  type = "zip"
  source {
    content  = file("${path.module}/../backend/index.py")
    filename = "index.py"
  }
  source {
    content  = file("${path.module}/../backend/requirements.txt")
    filename = "requirements.txt"
  }
  output_path = "${path.module}/function.zip"
}
resource "yandex_function" "contact" {
  name               = var.name
  runtime            = "python312"
  entrypoint         = "index.handler"
  memory             = 256
  execution_timeout  = 10
  service_account_id = yandex_iam_service_account.function.id
  user_hash          = data.archive_file.function.output_base64sha256
  content { zip_filename = data.archive_file.function.output_path }
  environment = {
    YDB_ENDPOINT    = "grpcs://${yandex_ydb_database_serverless.contact.ydb_api_endpoint}"
    YDB_DATABASE    = yandex_ydb_database_serverless.contact.database_path
    ALLOWED_ORIGINS = join(",", var.allowed_origins)
    IP_HASH_SECRET  = random_password.ip_hash.result
  }
  depends_on = [yandex_ydb_table.submissions, yandex_ydb_table.rate_limits, yandex_ydb_database_iam_binding.writer]
}
resource "yandex_function_iam_binding" "invoke" {
  function_id = yandex_function.contact.id
  role        = "functions.functionInvoker"
  members     = ["serviceAccount:${yandex_iam_service_account.gateway.id}"]
}
resource "yandex_api_gateway" "contact" {
  name = var.name
  spec = jsonencode({
    openapi = "3.0.0"
    info    = { title = "Contact submissions", version = "1.0.0" }
    paths = {
      "/submissions" = {
        for method in ["post", "options"] : method => {
          operationId = "${method}Submission"
          responses   = { "200" = { description = "Saved" } }
          "x-yc-apigateway-integration" = {
            type               = "cloud_functions"
            function_id        = yandex_function.contact.id
            service_account_id = yandex_iam_service_account.gateway.id
          }
        }
      }
    }
  })
  depends_on = [yandex_function_iam_binding.invoke]
}
output "contact_api_url" { value = "https://${yandex_api_gateway.contact.domain}/submissions" }
