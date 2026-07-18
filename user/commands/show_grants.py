"""
commands/show_grants.py — user.show_grants plugin function.

Shows all grants for a MySQL user account across one or all hosts.
"""
from mysqlsh.plugin_manager import plugin_function

from lib.session import require_session
from lib.parser import parse_user_host
from lib.output import print_section


@plugin_function("user.show_grants")
def show_grants(target_user, session=None):
    """
    Shows grants for a user across all hosts, or a specific host if provided.

    If no host is included in target_user, all matching accounts are shown.
    Output format mirrors SHOW GRANTS style.

    Args:
        target_user (string): The user to show grants for.
                              Use 'user' for all hosts or 'user@host' for
                              a specific host.
        session (object): The session to be used on the operation.
    """
    session = require_session(session)
    if session is None:
        return

    try:
        _, u, h = parse_user_host(target_user)

        if h is not None:
            # Specific host supplied — check exactly that account.
            accounts = [("'{}'@'{}'".format(u, h), u, h)]
        else:
            # No host supplied — resolve all hosts for this username.
            result = session.run_sql(
                "SELECT host FROM mysql.user WHERE user = '{}'".format(u)
            )
            rows = result.fetch_all()
            if not rows:
                print("User '{}' not found.".format(u))
                return
            accounts = [("'{}'@'{}'".format(u, row[0]), u, row[0]) for row in rows]

        for user_host, _u, _h in accounts:
            print_section("Grants for {}:".format(user_host))
            grants_res = session.run_sql("SHOW GRANTS FOR {}".format(user_host))
            for row in grants_res.fetch_all():
                print(row[0])

    except Exception as e:
        print("Error showing grants: {}".format(e))
