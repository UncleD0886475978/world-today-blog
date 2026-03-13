FROM registry.access.redhat.com/ubi9/python-311:latest
USER root
RUN dnf install -y git && dnf clean all
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY generate_posts.py .
COPY scheduler.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
RUN mkdir -p /app/blog_repo && chown -R 1001:1001 /app/blog_repo
USER 1001
ENTRYPOINT ["./entrypoint.sh"]
