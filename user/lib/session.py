"""
lib/session.py — Session resolution helper.

All commands call require_session() so the "no active session" guard
lives in exactly here.
"""
import mysqlsh


def require_session(session=None):
    """
    Returns a valid MySQL session or prints an error and returns None.

    Args:
        session: An already-resolved session, or None to auto-resolve
                 from the current shell globals.

    Returns:
        A live session object, or None if no session is available.
    """
    if session is not None:
        return session
    s = mysqlsh.globals.shell.get_session()
    if s is None:
        print("No active session. Please connect to a database first.")
    return s
