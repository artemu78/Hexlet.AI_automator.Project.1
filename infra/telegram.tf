variable "bot_token" {
  type      = string
  sensitive = true
  nullable  = false
  validation {
    condition     = length(trimspace(var.bot_token)) > 0
    error_message = "Set BOT_TOKEN or bot_token in deploy.local.json."
  }
}
variable "admin_chat_id" {
  type     = string
  nullable = false
  validation {
    condition     = length(trimspace(var.admin_chat_id)) > 0
    error_message = "Set ADMIN_CHAT_ID or admin_chat_id in deploy.local.json."
  }
}
data "archive_file" "telegram" {
  type = "zip"
  source {
    content  = file("${path.module}/../backend/telegram_function.py")
    filename = "telegram_function.py"
  }
  output_path = "${path.module}/telegram.zip"
}
resource "yandex_function" "telegram" {
  name              = "${var.name}-telegram"
  runtime           = "python312"
  entrypoint        = "telegram_function.handler"
  memory            = 128
  execution_timeout = 15
  user_hash         = data.archive_file.telegram.output_base64sha256
  content { zip_filename = data.archive_file.telegram.output_path }
  environment = {
    BOT_TOKEN     = var.bot_token
    ADMIN_CHAT_ID = var.admin_chat_id
  }
}
resource "yandex_function_iam_binding" "telegram_public" {
  function_id = yandex_function.telegram.id
  role        = "functions.functionInvoker"
  members     = ["system:allUsers"]
}
output "telegram_function_url" {
  value = "https://functions.yandexcloud.net/${yandex_function.telegram.id}"
}
