from .base import *  # noqa: F401, F403

# Override SECRET_KEY so tests are never affected by the local .env value.
# Must be ≥32 bytes to satisfy JWT's HMAC-SHA256 minimum and avoid warnings.
SECRET_KEY = "test-only-secret-key-not-used-in-production-xk9mQ2vLpR"  # noqa: S105

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use synchronous Celery for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
