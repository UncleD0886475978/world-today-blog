terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

provider "github" {
  token = var.github_token
  owner = var.github_username
}

resource "github_repository" "blog" {
  name        = var.repo_name
  description = "The World Today — Independent Global Journalism"
  visibility  = "public"
  auto_init   = true
  pages {
    source {
      branch = "main"
      path   = "/"
    }
  }
  topics = ["blog", "geopolitics", "history", "current-events", "jekyll"]
}

resource "github_actions_secret" "gemini_key" {
  repository      = github_repository.blog.name
  secret_name     = "GEMINI_API_KEY"
  plaintext_value = var.gemini_api_key
}

resource "docker_image" "blog_generator" {
  name = "world-today-blog:latest"
  build {
    context    = var.project_dir
    dockerfile = "Dockerfile"
  }
  triggers = {
    dockerfile     = filemd5("${var.project_dir}/Dockerfile")
    generate_posts = filemd5("${var.project_dir}/generate_posts.py")
    scheduler      = filemd5("${var.project_dir}/scheduler.py")
    requirements   = filemd5("${var.project_dir}/requirements.txt")
    entrypoint     = filemd5("${var.project_dir}/entrypoint.sh")
  }
}

resource "docker_volume" "blog_repo" {
  name = "world-today-blog-repo"
}

resource "docker_container" "blog_generator" {
  name    = "world-today-blog"
  image   = docker_image.blog_generator.image_id
  restart = "unless-stopped"
  env = [
    "GEMINI_API_KEY=${var.gemini_api_key}",
    "GITHUB_REPO_URL=https://${var.github_token}@github.com/${var.github_username}/${var.repo_name}.git",
    "GITHUB_USER_NAME=${var.git_user_name}",
    "GITHUB_USER_EMAIL=${var.git_user_email}",
    "SUBSTACK_URL=${var.substack_url}",
    "SUBSTACK_RSS=${var.substack_rss_feed}",
    "TWITTER_API_KEY=${var.twitter_api_key}",
    "TWITTER_API_SECRET=${var.twitter_api_secret}",
    "TWITTER_ACCESS_TOKEN=${var.twitter_access_token}",
    "TWITTER_ACCESS_SECRET=${var.twitter_access_secret}",
    "FACEBOOK_PAGE_TOKEN=${var.facebook_page_token}",
    "FACEBOOK_PAGE_ID=${var.facebook_page_id}",
    "THREADS_TOKEN=${var.threads_token}",
  ]
  volumes {
    volume_name    = docker_volume.blog_repo.name
    container_path = "/app/blog_repo"
  }
  volumes {
    host_path      = "${var.project_dir}/logs"
    container_path = "/app/logs"
  }
  log_opts = {
    "max-size" = "10m"
    "max-file" = "5"
  }
  depends_on = [docker_image.blog_generator]
}
