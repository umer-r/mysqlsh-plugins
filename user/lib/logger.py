"""
lib/logger.py — File logging for user plugin operations.

All file I/O for audit logging lives here so the path and format are
defined in a single place.
"""
import os
from datetime import datetime

_LOG_DIR = os.path.expanduser("~/.mysqlsh/plugins/user/logs")
_LOG_FILE = os.path.join(_LOG_DIR, "user_plugin.log")


def _ensure_log_dir():
    os.makedirs(_LOG_DIR, exist_ok=True)


def log(message):
    """
    Append a timestamped message to the plugin log file.

    Args:
        message (str): The message to log.
    """
    _ensure_log_dir()
    with open(_LOG_FILE, "a") as f:
        f.write("[{}] {}\n".format(datetime.now(), message))


def log_created_user(user_host, password, grants, server_connection=None):
    """
    Log a successful user creation event.

    Args:
        user_host (str): The full 'user'@'host' identifier.
        password (str): The password that was set (plaintext — keep log secure).
        grants (list): List of raw grant strings that were applied.
        server_connection (str, optional): Server connection where the user was created.
    """
    if server_connection:
        log("Created user: {}, password: {}, grants: {}, server: {}".format(
            user_host, password, grants, server_connection
        ))
    else:
        log("Created user: {}, password: {}, grants: {}".format(
            user_host, password, grants
        ))


def log_synced_grants(origin, destination, count):
    """
    Log a grant-sync operation.

    Args:
        origin (str): Source user identifier.
        destination (str): Destination user identifier.
        count (int): Number of GRANT statements applied.
    """
    log("Synced {} grant(s) from {} to {}".format(count, origin, destination))


def log_deleted_users(users_list):
    """
    Log user deletion events.

    Args:
        users_list (list): List of user_host identifiers deleted.
    """
    log("Deleted user(s): {}".format(", ".join(users_list)))

