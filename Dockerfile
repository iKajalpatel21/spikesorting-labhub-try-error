# ============================================================
# SpikesortingLabHub — Production Image
#
# Self-contained: clones the repo from GitHub so anyone can
# reproduce this image without needing the local source tree.
# ============================================================

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# 1. System packages
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.13 \
        python3.13-venv \
        python3-pip \
        build-essential \
        libpq-dev \
        openssl \
        ca-certificates \
        curl \
        git \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1 \
 && update-alternatives --install /usr/bin/python  python  /usr/bin/python3.13 1

# ------------------------------------------------------------
# 2. Clone repository and check out the docker branch
# ------------------------------------------------------------
WORKDIR /app
RUN git clone --branch docker https://github.com/iKajalpatel21/spikesorting-labhub-tryerror.git .

# ------------------------------------------------------------
# 3. Set up Python virtual environment and install requirements
# ------------------------------------------------------------
RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

ENV PATH="/app/venv/bin:$PATH"

# ------------------------------------------------------------
# 4. Build the React frontend
#    my-app/build/ is gitignored so it must be compiled here.
# ------------------------------------------------------------
RUN cd my-app && npm ci --omit=dev && npm run build

# ------------------------------------------------------------
# 5. Placeholder directories for bind mounts
#    Docker Compose overlays the real host paths at runtime.
#    /data        ← trurnasdata (read-only NAS database)
#    /django_db   ← persistentdata (Django SQLite DB + logs)
#    /experiments ← binary recording files (read-only)
# ------------------------------------------------------------
RUN mkdir -p /data /django_db /experiments /app/secrets

# ------------------------------------------------------------
# 6. Entrypoint — already in the repo after git clone.
#    Runs collectstatic + migrate before handing off to Gunicorn.
# ------------------------------------------------------------
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# ------------------------------------------------------------
# 7. Expose ports
#    9000 — plain HTTP
#    9443 — HTTPS (Gunicorn with --certfile / --keyfile)
# ------------------------------------------------------------
EXPOSE 9000 9443

# ------------------------------------------------------------
# 8. Default command — passed to entrypoint.sh via exec "$@".
# ------------------------------------------------------------
CMD ["gunicorn", "-c", "gunicorn.conf.py", "labhub.wsgi:application"]
