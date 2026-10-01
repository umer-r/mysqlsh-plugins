"""
lib/parse_grants.py — MySQL grant parsing and validation utilities.

Validates syntax, privileges, scopes, and target objects (db, db.table, *).
Supports table-level grants, global grants, and replication user keywords.
"""

TABLE_AND_DB_PRIVILEGES = {
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE",
    "DROP",
    "GRANT OPTION",
    "INDEX",
    "ALTER",
    "REFERENCES",
    "TRIGGER",
    "CREATE VIEW",
    "SHOW VIEW",
    "EXECUTE",
    "ALTER ROUTINE",
    "CREATE ROUTINE",
    "EVENT",
    "CREATE TEMPORARY TABLES",
    "LOCK TABLES",
}

GLOBAL_ONLY_PRIVILEGES = {
    "FILE",
    "PROCESS",
    "RELOAD",
    "SHUTDOWN",
    "SHOW DATABASES",
    "SUPER",
    "REPLICATION CLIENT",
    "REPLICATION SLAVE",
    "CREATE USER",
    "CREATE TABLESPACE",
    "CREATE ROLE",
    "DROP ROLE",
    "USAGE",
    # Dynamic privileges (MySQL 8.0+)
    "APPLICATION_PASSWORD_ADMIN",
    "AUDIT_ABORT_EXEMPT",
    "AUDIT_ADMIN",
    "AUTHENTICATION_POLICY_ADMIN",
    "BACKUP_ADMIN",
    "BINLOG_ADMIN",
    "BINLOG_ENCRYPTION_ADMIN",
    "CLONE_ADMIN",
    "CONNECTION_ADMIN",
    "ENCRYPTION_KEY_ADMIN",
    "FIREWALL_ADMIN",
    "FIREWALL_EXEMPT",
    "FLUSH_OPTIMIZER_COSTS",
    "FLUSH_STATUS",
    "FLUSH_TABLES",
    "FLUSH_USER_RESOURCES",
    "GROUP_REPLICATION_ADMIN",
    "GROUP_REPLICATION_STREAM",
    "INNODB_REDO_LOG_ARCHIVE",
    "INNODB_REDO_LOG_ENABLE",
    "MASKING_DICTIONARIES_ADMIN",
    "PASSWORD_LESS_USER_ADMIN",
    "PERSIST_RO_VARIABLES_ADMIN",
    "REPLICATION_APPLIER",
    "REPLICATION_SLAVE_ADMIN",
    "RESOURCE_GROUP_ADMIN",
    "RESOURCE_GROUP_USER",
    "ROLE_ADMIN",
    "SENSITIVE_VARIABLES_OBSERVER",
    "SERVICE_CONNECTION_ADMIN",
    "SESSION_VARIABLES_ADMIN",
    "SET_USER_ID",
    "SHOW_ROUTINE",
    "SYSTEM_USER",
    "SYSTEM_VARIABLES_ADMIN",
    "TABLE_ENCRYPTION_ADMIN",
    "TELEMETRY_ADMIN",
    "TRANSACTION_GTID_TAG",
    "VERSION_TOKEN_ADMIN",
    "XA_RECOVER_ADMIN",
}

ALL_PRIVILEGES = {"ALL", "ALL PRIVILEGES"}
REPLICATION_KEYWORDS = {"REPLICATION", "REPL"}


def _strip_quotes(s):
    return s.strip().strip("'").strip('"').strip('`')


def _normalize_and_validate_privilege(raw_priv):
    p = raw_priv.strip().upper()
    if not p:
        raise ValueError("Privilege name cannot be empty.")

    if p in ALL_PRIVILEGES:
        return "ALL PRIVILEGES"

    if p in TABLE_AND_DB_PRIVILEGES or p in GLOBAL_ONLY_PRIVILEGES:
        return p

    # Support underscore variations for multi-word privileges (e.g. REPLICATION_SLAVE -> REPLICATION SLAVE)
    p_space = p.replace("_", " ")
    if p_space in TABLE_AND_DB_PRIVILEGES or p_space in GLOBAL_ONLY_PRIVILEGES:
        return p_space

    # Support space variations for dynamic privileges (e.g. SYSTEM USER -> SYSTEM_USER)
    p_underscore = p.replace(" ", "_")
    if p_underscore in GLOBAL_ONLY_PRIVILEGES or p_underscore in TABLE_AND_DB_PRIVILEGES:
        return p_underscore

    raise ValueError(f"Invalid privilege '{raw_priv}'. Not a supported MySQL privilege.")


def _parse_target(raw_target):
    t = raw_target.strip()
    if not t:
        raise ValueError("Target cannot be empty. Expected format: db.table, db.*, or *.*")

    if t in ("*", "*.*"):
        return "*.*"

    if "." in t:
        parts = t.split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid target '{raw_target}'. Expected format: db.table, db.*, or *.*")
        db = _strip_quotes(parts[0])
        table = _strip_quotes(parts[1])
        if not db:
            raise ValueError(f"Database name cannot be empty in '{raw_target}'.")
        if not table:
            raise ValueError(f"Table name cannot be empty in '{raw_target}'.")
        if table == "*":
            return f"`{db}`.*"
        else:
            return f"`{db}`.`{table}`"
    else:
        db = _strip_quotes(t)
        if not db:
            raise ValueError("Target cannot be empty.")
        if db == "*":
            return "*.*"
        return f"`{db}`.*"


def parse_grant(grant_str):
    """
    Parses and validates a grant specification into SQL-ready privileges and target.

    Supported syntax:
      - grant,grant,...:db.table|*
      - ALL:db.table|*
      - INSERT,UPDATE,DELETE:db.table  (table-level)
      - REPLICATION or REPL             (replication user shortcut)
      - REPLICATION:* or REPL:*

    Args:
        grant_str (str): The raw grant string to parse.

    Returns:
        tuple: (privileges_str, target_str)
               e.g. ("INSERT, UPDATE", "`mydb`.`mytable`")
                    ("ALL PRIVILEGES", "`mydb`.*")
                    ("REPLICATION SLAVE, REPLICATION CLIENT", "*.*")

    Raises:
        ValueError: If the syntax or privilege is invalid.
    """
    if not grant_str or not isinstance(grant_str, str) or not grant_str.strip():
        raise ValueError("Grant string cannot be empty.")

    cleaned = grant_str.strip()

    # 1. Check for replication keyword shortcut
    upper_cleaned = cleaned.upper()
    if upper_cleaned in REPLICATION_KEYWORDS:
        return "REPLICATION SLAVE, REPLICATION CLIENT", "*.*"

    if ":" in cleaned:
        raw_privs, raw_target = cleaned.split(":", 1)
        raw_privs = raw_privs.strip()
        raw_target = raw_target.strip()
    else:
        # Check if entire string is ALL
        if upper_cleaned in ALL_PRIVILEGES:
            return "ALL PRIVILEGES", "*.*"
        raise ValueError(
            f"Invalid grant format '{grant_str}'. Expected format: 'grant,grant:db.table|*' or 'ALL:db.table|*'"
        )

    if not raw_privs:
        raise ValueError(f"Privileges cannot be empty in '{grant_str}'.")
    if not raw_target:
        raise ValueError(f"Target cannot be empty in '{grant_str}'.")

    # Check if raw_privs is a replication keyword e.g. "REPLICATION:*"
    if raw_privs.upper() in REPLICATION_KEYWORDS:
        target = _parse_target(raw_target)
        if target != "*.*":
            raise ValueError(f"Replication privileges can only be granted globally (*.*), not on '{target}'.")
        return "REPLICATION SLAVE, REPLICATION CLIENT", "*.*"

    # Parse and validate target
    target = _parse_target(raw_target)

    # Parse and validate individual privileges
    raw_priv_list = [p.strip() for p in raw_privs.split(",") if p.strip()]
    if not raw_priv_list:
        raise ValueError(f"No privileges found in '{grant_str}'.")

    validated_privs = []
    for rp in raw_priv_list:
        norm_p = _normalize_and_validate_privilege(rp)

        # Check scope: global-only privileges cannot be granted on db or table
        if target != "*.*" and norm_p in GLOBAL_ONLY_PRIVILEGES:
            raise ValueError(
                f"Privilege '{norm_p}' can only be granted globally (*.*), not on '{target}'."
            )
        validated_privs.append(norm_p)

    # If ALL PRIVILEGES is in list, normalize to ALL PRIVILEGES
    if "ALL PRIVILEGES" in validated_privs:
        privileges_str = "ALL PRIVILEGES"
    else:
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for p in validated_privs:
            if p not in seen:
                seen.add(p)
                deduped.append(p)
        privileges_str = ", ".join(deduped)

    return privileges_str, target


def parse_grants(grants_input):
    """
    Parses and validates one or multiple grant specifications.

    Args:
        grants_input (list or str): A list of grant strings, or a semicolon/newline
                                    delimited string of grant specifications.

    Returns:
        list of tuple: List of (privileges_str, target_str)
    """
    if not grants_input:
        return []

    if isinstance(grants_input, str):
        if ";" in grants_input:
            items = [item.strip() for item in grants_input.split(";") if item.strip()]
        elif "\n" in grants_input:
            items = [item.strip() for item in grants_input.split("\n") if item.strip()]
        else:
            items = [grants_input.strip()]
    elif isinstance(grants_input, (list, tuple)):
        items = grants_input
    else:
        raise ValueError("grants_input must be a string or list of strings.")

    return [parse_grant(item) for item in items if item]
