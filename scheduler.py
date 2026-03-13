#!/usr/bin/env python3
import os, subprocess, schedule, time, datetime, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s  [%(levelname)s]  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

GITHUB_REPO_URL   = os.environ["GITHUB_REPO_URL"]
GITHUB_USER_NAME  = os.environ["GITHUB_USER_NAME"]
GITHUB_USER_EMAIL = os.environ["GITHUB_USER_EMAIL"]
REPO_DIR          = "/app/blog_repo"

def setup_repo():
    if os.path.exists(os.path.join(REPO_DIR, ".git")):
        log.info("Repo already cloned — pulling latest...")
        subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)
    else:
        log.info("Cloning repo...")
        subprocess.run(["git", "clone", GITHUB_REPO_URL, REPO_DIR], check=True)
    subprocess.run(["git", "-C", REPO_DIR, "config", "user.name",  GITHUB_USER_NAME],  check=True)
    subprocess.run(["git", "-C", REPO_DIR, "config", "user.email", GITHUB_USER_EMAIL], check=True)
    log.info("Repo ready.")

def generate_and_push():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    log.info(f"=== Starting post generation: {now} ===")
    try:
        subprocess.run(["git", "-C", REPO_DIR, "pull", "--rebase"], check=True)
    except:
        log.warning("git pull failed — continuing.")
    env = os.environ.copy()
    env["POSTS_OUTPUT_DIR"] = os.path.join(REPO_DIR, "_posts")
    result = subprocess.run(["python", "/app/generate_posts.py"], env=env, capture_output=True, text=True)
    log.info(result.stdout)
    if result.returncode != 0:
        log.error(f"generate_posts.py failed:\n{result.stderr}")
        return
    try:
        subprocess.run(["git", "-C", REPO_DIR, "add", "_posts/"], check=True)
        diff = subprocess.run(["git", "-C", REPO_DIR, "diff", "--staged", "--quiet"])
        if diff.returncode == 0:
            log.info("Nothing new to commit.")
            return
        subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", f"Auto-post: {now}"], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "push"], check=True)
        log.info("Posts pushed to GitHub successfully.")
    except subprocess.CalledProcessError as e:
        log.error(f"Git push failed: {e}")

def main():
    log.info("Scheduler Starting")
    setup_repo()
    schedule.every().day.at("07:00").do(generate_and_push)
    schedule.every().day.at("13:00").do(generate_and_push)
    schedule.every().day.at("19:00").do(generate_and_push)
    log.info("Running immediate test generation...")
    generate_and_push()
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
