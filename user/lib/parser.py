"""
lib/parser.py — User / host string parsing utilities.

Centralises all quoting and splitting logic so commands don't each
re-implement the same string manipulation.
"""


def parse_user_host(user_str):
    """
    Parse a 'user' or 'user@host' string into a quoted identifier tuple.

    Args:
        user_str (str): A plain username or 'user@host' string, with any
                        surrounding quotes stripped automatically.

    Returns:
        tuple: (full_identifier, username, host_or_None)
               full_identifier is SQL-ready (e.g. ``'alice'@'%'``).
               host is None when no @ was present.
    """
    def _strip_quotes(s):
        return s.strip().strip("'").strip('"').strip('`')

    if '@' in user_str:
        raw_u, raw_h = user_str.split('@', 1)
        u = _strip_quotes(raw_u)
        h = _strip_quotes(raw_h)
        return "'{}'@'{}'".format(u, h), u, h
    else:
        u = _strip_quotes(user_str)
        return "'{}'".format(u), u, None


def resolve_single_host(session, username, label="User"):
    """
    Look up the single host for a username that exists in mysql.user.

    Prints an error and returns None when the user is missing or has
    multiple hosts (caller should use 'user@host' in that case).

    Args:
        session: Active MySQL session.
        username (str): The plain username to look up.
        label (str): Human-readable label used in error messages
                     (e.g. 'Origin', 'Destination').

    Returns:
        str: The host value, or None on error.
    """
    result = session.run_sql(
        "SELECT host FROM mysql.user WHERE user = '{}'".format(username)
    )
    rows = result.fetch_all()
    if not rows:
        print("{} user '{}' not found.".format(label, username))
        return None
    if len(rows) > 1:
        print(
            "Multiple hosts found for {} user '{}'. "
            "Please specify using 'user@host'.".format(label, username)
        )
        return None
    return rows[0][0]
