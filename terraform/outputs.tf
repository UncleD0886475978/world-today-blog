# ── OUTPUTS ───────────────────────────────────────────────────────────────────
# Printed to terminal after `terraform apply` completes

output "blog_url" {
  description = "Your live GitHub Pages blog URL"
  value       = "https://${var.github_username}.github.io/${var.repo_name}"
}

output "github_repo_url" {
  description = "GitHub repository URL"
  value       = github_repository.blog.html_url
}

output "container_name" {
  description = "Docker container name"
  value       = docker_container.blog_generator.name
}

output "container_id" {
  description = "Docker container ID"
  value       = docker_container.blog_generator.id
}

output "docker_volume" {
  description = "Persistent Docker volume name for the cloned repo"
  value       = docker_volume.blog_repo.name
}

output "next_steps" {
  description = "What to do after apply"
  value       = <<-EOT

    ✓ Infrastructure deployed successfully!

    Your blog:     https://${var.github_username}.github.io/${var.repo_name}
    GitHub repo:   ${github_repository.blog.html_url}
    Container:     ${docker_container.blog_generator.name} (running)

    Useful commands:
      View live logs:   docker logs -f ${docker_container.blog_generator.name}
      Trigger manually: docker exec ${docker_container.blog_generator.name} python /app/generate_posts.py
      Stop container:   terraform destroy (or: docker stop ${docker_container.blog_generator.name})

    Posts publish at 07:00, 13:00, and 19:00 UTC daily.
  EOT
}
