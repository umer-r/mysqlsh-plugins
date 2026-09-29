"""
commands/rotate_pass.py — user.rotate_pass plugin function.

Rotates password for a MySQL user account across one or all hosts with confirmation.
"""
import mysqlsh
from mysqlsh.plugin_manager import plugin_function

from lib.session import require_session, get_server_connection
from lib.parser import parse_user_host
from lib.logger import log_rotated_password
from lib.output import print_table
from lib.password import generate_password


@plugin_function("user.rotate_pass")
def rotate_pass(target_user=None, session=None):
    """
    Rotates the password for a user account across one or all hosts.

    Single password rotation syntax:
      ALTER USER 'user'@'host' IDENTIFIED BY 'new_pass';

    Prompts for username (if not supplied), password (or auto-generates if empty),
    and target host(s) (or all hosts where the user exists).
    As this is a destructive process, a confirmation prompt is shown with
    the exact ALTER USER statements that will be run.

    Args:
        target_user (string, optional): The user to rotate password for.
                                        Can be 'user' or 'user@host'.
        session (object, optional): The session to be used on the operation.
    """
    shell = mysqlsh.globals.shell
    session = require_session(session)
    if session is None:
        return

    # ── 1. Resolve username and host input ───────────────────────────────────
    if target_user:
        _, u, h = parse_user_host(target_user)
    else:
        username_raw = shell.prompt("username: ").strip()
        if not username_raw:
            print("Username cannot be empty.")
            return
        _, u, h = parse_user_host(username_raw)

    if not u:
        print("Username cannot be empty.")
        return

    # ── 2. Password input / auto-generation ──────────────────────────────────
    password = shell.prompt("password [return for auto generated]: ").strip()
    if not password:
        password = generate_password()

    # ── 3. Host input and account resolution ─────────────────────────────────
    if h is not None:
        hosts = [h]
    else:
        hosts_raw = shell.prompt("host [comma separated, return for all hosts]: ").strip()
        if hosts_raw:
            hosts = [part.strip() for part in hosts_raw.split(',') if part.strip()]
        else:
            hosts = None

    try:
        users_to_rotate = []
        if hosts is not None:
            for h_item in hosts:
                full_ident, _, clean_h = parse_user_host("{}@{}".format(u, h_item))
                result = session.run_sql(
                    "SELECT 1 FROM mysql.user WHERE user = '{}' AND host = '{}'".format(u, clean_h)
                )
                if not result.fetch_all():
                    print("User {} not found.".format(full_ident))
                    return
                users_to_rotate.append((full_ident, u, clean_h))
        else:
            result = session.run_sql(
                "SELECT host FROM mysql.user WHERE user = '{}'".format(u)
            )
            rows = result.fetch_all()
            if not rows:
                print("User '{}' not found on any host.".format(u))
                return
            users_to_rotate = [
                parse_user_host("{}@{}".format(u, row[0])) for row in rows
            ]

        # ── 4. Display preview, commands and warning ─────────────────────────
        commands_to_run = [
            "ALTER USER {} IDENTIFIED BY '{}';".format(user_host, password)
            for user_host, _, _ in users_to_rotate
        ]

        print("\n" + "=" * 60)
        print("CAUTION: You are about to ROTATE PASSWORD for the following account(s):")
        print("\nThe following command(s) will be executed:")
        for cmd in commands_to_run:
            print("  {}".format(cmd))
        print("\nThis operation is DESTRUCTIVE and will immediately overwrite existing password(s).")
        print("=" * 60 + "\n")

        confirm = shell.prompt(
            "Are you sure you want to proceed? [type 'yes' to confirm]: "
        ).strip().lower()
        if confirm != 'yes':
            print("Password rotation cancelled.")
            return

        # ── 5. Execute password rotation and logging ─────────────────────────
        server_conn = get_server_connection(session)
        rotated = []
        for user_host, user_name, host_name in users_to_rotate:
            session.run_sql(
                "ALTER USER {} IDENTIFIED BY '{}'".format(user_host, password)
            )
            log_rotated_password(user_host, password, server_conn)
            rotated.append((user_name, host_name, password))

        # ── 6. Display results ───────────────────────────────────────────────
        print("")
        print_table(
            headers=["user", "host", "new_password"],
            rows=[[un, hn, pw] for un, hn, pw in rotated],
        )
        print("\nSuccessfully rotated password for {} user(s).".format(len(rotated)))

    except Exception as e:
        print("Error rotating password: {}".format(e))
