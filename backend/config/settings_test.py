"""
Test settings configuration for Movona.

Inherits from default configuration and overrides PASSWORD_HASHERS
with MD5PasswordHasher for ultra-fast automated test suite execution.
Production and normal development environments continue to use Django's
secure default PBKDF2 password hasher.
"""

from .settings import *  # noqa: F401, F403

# Fast password hasher exclusively for automated test performance
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
