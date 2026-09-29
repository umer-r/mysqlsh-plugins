"""
commands/create.py — user.create plugin function.

Interactive wizard to create one or more MySQL user accounts.
"""
import mysqlsh
from mysqlsh.plugin_manager import plugin_function

from lib.session import require_session, get_server_connection
from lib.logger import log_created_user
from lib.output import print_table
from lib.password import generate_password


@plugin_function("user.create")
def create(session=None):
    """
    Wizard to create a user interactively.

    Prompts for username, hosts, password, and grants then creates the
    user account(s) and logs the results to
    ~/.mysqlsh/plugins/user/logs/user_plugin.log

    Args:
        session (object): The session to be used on the operation.
    """
    shell = mysqlsh.globals.shell
    session = require_session(session)
    if session is None:
        return

    server_conn = get_server_connection(session)

    # ── Collect input ────────────────────────────────────────────────────────
    username = shell.prompt("username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    hosts_raw = shell.prompt("hosts [separated by comma]: ").strip()
    hosts = [h.strip() for h in hosts_raw.split(',') if h.strip()] or ['%']

    password = shell.prompt(
        "password [Leave blank for random 16-char password]: "
    ).strip()
    if not password:
        password = generate_password()

    grants = []
    while True:
        grant = shell.prompt(
            "grants [e.g. INSERT,UPDATE:db_name | empty to finish]: "
        ).strip()
        if not grant:
            break
        grants.append(grant)

    # ── Execute ──────────────────────────────────────────────────────────────
    created = []  # (username, host, password)

    try:
        for host in hosts:
            user_host = "'{}'@'{}'".format(username, host)
            session.run_sql(
                "CREATE USER {} IDENTIFIED BY '{}'".format(user_host, password)
            )
            created.append((username, host, password))

            for grant in grants:
                if ':' in grant:
                    privs, db = grant.split(':', 1)
                    db = db.strip()
                    db_str = '*.*' if db == '*' else '`{}`.*'.format(db)
                    session.run_sql(
                        "GRANT {} ON {} TO {}".format(privs.strip(), db_str, user_host)
                    )
                else:
                    session.run_sql(
                        "GRANT {} ON *.* TO {}".format(grant, user_host)
                    )

            log_created_user(user_host, password, grants, server_conn)

    except Exception as e:
        print("Error creating user: {}".format(e))
        return

    # ── Display results ──────────────────────────────────────────────────────
    print("")
    print_table(
        headers=["user", "host", "generated_password"],
        rows=[[u, h, p] for u, h, p in created],
    )
