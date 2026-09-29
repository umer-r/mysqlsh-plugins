"""
commands/genpass.py — user.genpass plugin function.

Generates and outputs a random password containing alphanumeric and safe special characters.
"""
from mysqlsh.plugin_manager import plugin_function

from lib.password import generate_password, DEFAULT_PASSWORD_LENGTH


@plugin_function("user.genpass")
def genpass(length=DEFAULT_PASSWORD_LENGTH):
    """
    Generates and outputs a random password.

    Does not run any SQL or create audit logs.

    Args:
        length (int, optional): Length of the password (defaults to 16).

    Returns:
        str: The generated password.
    """
    password = generate_password(length=length)
    # print(password)
    return password
