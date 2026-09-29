"""
lib/password.py — Password generation utilities.

Centralizes random password generation logic for the user plugin.
"""
import string
import secrets

SAFE_SPECIAL_CHARS = "^#()[]{}<>+=-"
DEFAULT_PASSWORD_LENGTH = 16


def generate_password(length=DEFAULT_PASSWORD_LENGTH, special_chars=SAFE_SPECIAL_CHARS):
    """
    Generates a secure random password containing alphanumeric and safe special characters.

    Args:
        length (int): Length of the password to generate (defaults to 16).
        special_chars (str): String containing safe special characters to include.

    Returns:
        str: Randomly generated password.
    """
    alphabet = string.ascii_letters + string.digits + special_chars
    return ''.join(secrets.choice(alphabet) for _ in range(length))
