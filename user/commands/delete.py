"""
commands/delete.py — user.delete plugin function.

Deletes a MySQL user account across one or all hosts, with confirmation.
"""
import mysqlsh
from mysqlsh.plugin_manager import plugin_function

from lib.session import require_session
from lib.parser import parse_user_host
from lib.logger import log_deleted_users


@plugin_function("user.delete")
def delete(target_user, session=None):
    """
    Deletes a user account.

    If host is provided, deletes user on that specific host.
    If host is not provided, deletes user on all hosts where it exists.
    As this is a destructive process, a confirmation prompt is shown with
    the list of users to be deleted and an irreversible warning.

    Args:
        target_user (string): The user to delete. Use 'user' for all hosts or
                              'user@host' for a specific host.
        session (object): The session to be used on the operation.
    """
    shell = mysqlsh.globals.shell
    session = require_session(session)
    if session is None:
        return

    try:
        _, u, h = parse_user_host(target_user)

        # 1. Resolve users to be deleted
        users_to_delete = []
        if h is not None:
            # Check if this user exists
            result = session.run_sql(
                "SELECT 1 FROM mysql.user WHERE user = '{}' AND host = '{}'".format(u, h)
            )
            if result.fetch_all():
                users_to_delete.append(("'{}'@'{}'".format(u, h), u, h))
            else:
                print("User '{}'@'{}' not found.".format(u, h))
                return
        else:
            result = session.run_sql(
                "SELECT host FROM mysql.user WHERE user = '{}'".format(u)
            )
            rows = result.fetch_all()
            if not rows:
                print("User '{}' not found on any host.".format(u))
                return
            users_to_delete = [("'{}'@'{}'".format(u, row[0]), u, row[0]) for row in rows]

        # 2. Display preview and warning
        print("\n" + "=" * 60)
        print("CAUTION: You are about to DELETE the following user account(s):")
        for user_host, _, _ in users_to_delete:
            print("  - {}".format(user_host))
        print("\nThis is process is IRREVERSIBLE unless you have a backup.")
        print("=" * 60 + "\n")

        confirm = shell.prompt("Are you sure you want to proceed? [type 'yes' to confirm]: ").strip().lower()
        if confirm != 'yes':
            print("Deletion cancelled.")
            return

        # 3. Perform deletion
        deleted_users = []
        for user_host, _, _ in users_to_delete:
            session.run_sql("DROP USER {}".format(user_host))
            print("Deleted user: {}".format(user_host))
            deleted_users.append(user_host)

        log_deleted_users(deleted_users)
        print("\nSuccessfully deleted {} user(s).".format(len(deleted_users)))

    except Exception as e:
        print("Error deleting user: {}".format(e))
