# ── VARIABLE DEFINITIONS ──────────────────────────────────────────────────────
# Values are set in terraform.tfvars (never committed to git)

variable "gemini_api_key" {
  description = "Google Gemini API key from aistudio.google.com"
  type        = string
  sensitive   = true

}

variable "github_token" {
  description = "GitHub Personal Access Token with 'repo' scope"
  type        = string
  sensitive   = true
}

variable "github_username" {
  description = "Your GitHub username (e.g. worldtodayblog)"
  type        = string
}

variable "repo_name" {
  description = "GitHub repository name for the blog"
  type        = string
  default     = "world-today-blog"
}

variable "git_user_name" {
  description = "Name used in git commits (e.g. BlogBot)"
  type        = string
  default     = "BlogBot"
}

variable "git_user_email" {
  description = "Email used in git commits"
  type        = string
}

variable "project_dir" {
  description = "Absolute path to your blog project folder on disk (e.g. /home/youruser/world-today-blog)"
  type        = string
}
