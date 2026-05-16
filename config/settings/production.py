"""
Production settings — used on Railway / Render / any cloud host.

Required environment variables:
    SECRET_KEY       Django secret key (≥50 chars recommended)
    DATABASE_URL     Postgres connection string  (Railway sets this automatically)
    REDIS_URL        Redis connection string     (Railway sets this automatically)
    ALLOWED_HOSTS    Comma-separated list of allowed hostnames
"""
import dj_database_url

from .base import *  # noqa: F401, F403

DEBUG = False

# Parse DATABASE_URL if present (Railway, Render, Fly.io all set this)
import os

_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            _database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# Serve static files from STATIC_ROOT without a separate web server
MIDDLEWARE = ["whitenoise.middleware.WhiteNoiseMiddleware"] + MIDDLEWARE  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
