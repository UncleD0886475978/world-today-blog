terraform {
  required_version = ">= 1.5.0"

  required_providers {
    # Docker provider — manages containers on your local Red Hat machine
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    # GitHub provider — manages your repo, Pages, and branch settings
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

# ── PROVIDERS ─────────────────────────────────────────────────────────────────

provider "docker" {
  # Connects to the local Docker daemon on your Red Hat machine
  host = "unix:///var/run/docker.sock"
}

provider "github" {
  token = var.github_token
  owner = var.github_username
}

# ── GITHUB REPOSITORY ─────────────────────────────────────────────────────────

resource "github_repository" "blog" {
  name        = var.repo_name
  description = "The World Today — Automated Daily History & Geopolitics Blog"
  visibility  = "public"          # GitHub Pages requires public on free plan
  auto_init   = true              # Creates initial commit with README

  # Enable GitHub Pages source
  pages {
    source {
      branch = "main"
      path   = "/"
    }
  }

  topics = ["blog", "geopolitics", "history", "current-events", "jekyll"]
}

# ── GITHUB BRANCH PROTECTION ──────────────────────────────────────────────────

resource "github_branch_protection" "main" {
  repository_id = github_repository.blog.node_id
  pattern       = "main"

  # Allow the BlogBot to push posts without a pull request
  allows_force_pushes = false
  allows_deletions    = false
}

# ── GITHUB SECRETS ────────────────────────────────────────────────────────────
# Store the Anthropic API key in the repo (used if you ever switch back to
# GitHub Actions — harmless if you're Docker-only)

resource "github_actions_secret" "anthropic_key" {
  repository      = github_repository.blog.name
  secret_name     = "GEMINI_API_KEY"
 plaintext_value = var.gemini_api_key
}

# ── DOCKER: BUILD IMAGE ───────────────────────────────────────────────────────

resource "docker_image" "blog_generator" {
  name = "world-today-blog:latest"

  build {
    context    = var.project_dir   # Path to your blog project folder on disk
    dockerfile = "Dockerfile"
  }

  # Rebuild image if any source file changes
  triggers = {
    dockerfile        = filemd5("${var.project_dir}/Dockerfile")
    generate_posts    = filemd5("${var.project_dir}/generate_posts.py")
    scheduler         = filemd5("${var.project_dir}/scheduler.py")
    requirements      = filemd5("${var.project_dir}/requirements.txt")
    entrypoint        = filemd5("${var.project_dir}/entrypoint.sh")
  }
}

# ── DOCKER: PERSISTENT VOLUME ─────────────────────────────────────────────────

resource "docker_volume" "blog_repo" {
  name = "world-today-blog-repo"
  # Persists the cloned GitHub repo between container restarts
}

# ── DOCKER: CONTAINER ─────────────────────────────────────────────────────────

resource "docker_container" "blog_generator" {
  name  = "world-today-blog"
  image = docker_image.blog_generator.image_id

  # Always restart unless manually stopped
  restart = "unless-stopped"

  # Environment variables (secrets injected from terraform.tfvars)
  env = [
    "GEMINI_API_KEY=${var.gemini_api_key}",
    "GITHUB_REPO_URL=https://${var.github_token}@github.com/${var.github_username}/${var.repo_name}.git",
    "GITHUB_USER_NAME=${var.git_user_name}",
    "GITHUB_USER_EMAIL=${var.git_user_email}",
  ]

  # Mount the persistent volume for the cloned repo
  volumes {
    volume_name    = docker_volume.blog_repo.name
    container_path = "/app/blog_repo"
  }

  # Mount local logs directory for easy access
  volumes {
    host_path      = "${var.project_dir}/logs"
    container_path = "/app/logs"
  }

  # Log rotation
  log_opts = {
    "max-size" = "10m"
    "max-file" = "5"
  }

  # Depend on image being built first
  depends_on = [docker_image.blog_generator]
}
