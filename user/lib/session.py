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


def get_server_connection(session):
    """
    Returns a string identifying the server connection for the given session.

    Checks session properties (uri/get_uri) first, and falls back to
    querying @@hostname and @@port from the server.

    Args:
        session: Active MySQL session.

    Returns:
        str: Server connection details (e.g. 'root@localhost:3306'),
             or 'unknown' if it cannot be determined.
    """
    if session is None:
        return "unknown"

    # Try session.uri or session.get_uri()
    uri = getattr(session, 'uri', None)
    if uri:
        return str(uri)
    if hasattr(session, 'get_uri') and callable(session.get_uri):
        try:
            u = session.get_uri()
            if u:
                return str(u)
        except Exception:
            pass

    # Fallback to querying MySQL server globals
    try:
        res = session.run_sql("SELECT @@hostname, @@port")
        rows = res.fetch_all()
        if rows and len(rows[0]) >= 2:
            return "{}:{}".format(rows[0][0], rows[0][1])
    except Exception:
        pass

    return "unknown"

