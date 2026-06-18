"""
User authentication utilities.
"""
import hashlib
import re

<<<<<<< HEAD
MIN_PASSWORD_LENGTH = 10
MAX_LOGIN_ATTEMPTS = 3
=======
MIN_PASSWORD_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
>>>>>>> feature/relax-password-policy


def hash_password(password: str) -> str:
    """Return SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, error_message).
    """
<<<<<<< HEAD
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*]', password):
        return False, "Password must contain at least one special character (!@#$%^&*)"
=======
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
>>>>>>> feature/relax-password-policy
    return True, ""


def is_account_locked(failed_attempts: int) -> bool:
<<<<<<< HEAD
    """Return True if the account should be locked."""
    return failed_attempts >= MAX_LOGIN_ATTEMPTS
=======
    """Return True if account is locked due to too many failed login attempts."""
    return failed_attempts > MAX_LOGIN_ATTEMPTS
>>>>>>> feature/relax-password-policy
