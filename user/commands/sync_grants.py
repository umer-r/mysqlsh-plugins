"""
commands/sync_grants.py — user.sync_grants plugin function.

Copies all GRANT statements from one MySQL account to another.
"""
from mysqlsh.plugin_manager import plugin_function

from lib.session import require_session
from lib.parser import parse_user_host, resolve_single_host
from lib.logger import log_synced_grants


@plugin_function("user.sync_grants")
def sync_grants(users_dict, session=None):
    """
    Syncs grants from an origin user to a destination user.

    Fetches all grants from origin_user and applies equivalent grants to
    destination_user, replacing user references in the GRANT statements.

    Args:
        users_dict (dictionary): Dictionary with keys 'origin_user' and
                                 'destination_user'. Values can be 'user'
                                 or 'user@host'.
        session (object): The session to be used on the operation.
    """
    session = require_session(session)
    if session is None:
        return

    origin = users_dict.get('origin_user')
    dest = users_dict.get('destination_user')

    if not origin or not dest:
        print("Please provide both 'origin_user' and 'destination_user'.")
        return

    try:
        origin_full, origin_u, origin_h = parse_user_host(origin)
        dest_full, dest_u, dest_h = parse_user_host(dest)

        # Resolve host when only a bare username was given.
        if origin_h is None:
            origin_h = resolve_single_host(session, origin_u, label="Origin")
            if origin_h is None:
                return
            origin_full = "'{}'@'{}'".format(origin_u, origin_h)

        if dest_h is None:
            dest_h = resolve_single_host(session, dest_u, label="Destination")
            if dest_h is None:
                return
            dest_full = "'{}'@'{}'".format(dest_u, dest_h)

        # Fetch and rewrite GRANT statements.
        grants_res = session.run_sql("SHOW GRANTS FOR {}".format(origin_full))
        grants = [row[0] for row in grants_res.fetch_all()]

        print("Syncing grants from {} to {}...".format(origin_full, dest_full))

        applied = 0
        for grant in grants:
            new_grant = grant
            for orig_sig in [
                "`{}`@`{}`".format(origin_u, origin_h),
                "'{}'@'{}'".format(origin_u, origin_h),
            ]:
                new_grant = new_grant.replace(
                    orig_sig, "`{}`@`{}`".format(dest_u, dest_h)
                )

            if new_grant != grant:
                try:
                    session.run_sql(new_grant)
                    print("  OK: {}".format(new_grant))
                    applied += 1
                except Exception as ex:
                    print("  FAIL: {}\n  Error: {}".format(new_grant, ex))

        log_synced_grants(origin_full, dest_full, applied)
        print("Sync complete. {} grant(s) applied.".format(applied))

    except Exception as e:
        print("Error syncing grants: {}".format(e))
