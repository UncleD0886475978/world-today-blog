variable "gemini_api_key" {
  description = "Google Gemini API key from aistudio.google.com"
  type        = string
  sensitive   = true
}
variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
}
variable "github_username" {
  description = "Your GitHub username"
  type        = string
}
variable "repo_name" {
  description = "GitHub repository name"
  type        = string
  default     = "world-today-blog"
}
variable "git_user_name" {
  description = "Name used in git commits"
  type        = string
  default     = "BlogBot"
}
variable "git_user_email" {
  description = "Email used in git commits"
  type        = string
}
variable "project_dir" {
  description = "Absolute path to your blog project folder"
  type        = string
}
variable "substack_url" {
  description = "Your Substack publication URL"
  type        = string
  default     = ""
}
variable "substack_rss_feed" {
  description = "Your blog RSS feed URL for Substack"
  type        = string
  default     = ""
}
variable "twitter_api_key" {
  description = "Twitter API key"
  type        = string
  default     = ""
  sensitive   = true
}
variable "twitter_api_secret" {
  description = "Twitter API secret"
  type        = string
  default     = ""
  sensitive   = true
}
variable "twitter_access_token" {
  description = "Twitter access token"
  type        = string
  default     = ""
  sensitive   = true
}
variable "twitter_access_secret" {
  description = "Twitter access token secret"
  type        = string
  default     = ""
  sensitive   = true
}
variable "facebook_page_token" {
  description = "Facebook Page access token"
  type        = string
  default     = ""
  sensitive   = true
}
variable "facebook_page_id" {
  description = "Facebook Page ID"
  type        = string
  default     = ""
}
variable "threads_token" {
  description = "Threads API token"
  type        = string
  default     = ""
  sensitive   = true
}
