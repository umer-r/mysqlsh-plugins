# MySQL Shell User Account Management Plugin

A modular, scalable user management plugin for **MySQL Shell 9.x**. It provides a set of helper functions to interactively create users, inspect permissions, sync permissions between users, and safely delete accounts.

---

## Features

- **`user.create()`**: Interactive wizard to create users across multiple hosts, automatically generate secure passwords, apply structured database privileges, output a visual ASCII results table, and record additions to an audit log.
- **`user.show_grants(target_user)`**: Quickly inspect grants for a user. If only a username is provided (e.g. `'alice'`), displays grants for all hosts. If `'alice@localhost'` is provided, displays grants for that specific host only.
- **`user.sync_grants(users_dict)`**: Synchronizes grants from an origin user to a destination user (e.g. `{'origin_user': 'alice', 'destination_user': 'bob'}`), automatically rewriting host signatures.
- **`user.delete(target_user)`**: Safely removes a user account. If no host is specified, resolves all hosts where the user exists, prints a clear warning warning of irreversible deletion, and prompts for explicit confirmation before executing `DROP USER`.
- **`user.rotate_pass()`**: Safely rotates user account passwords across one or all hosts using single password rotation syntax (`ALTER USER ... IDENTIFIED BY`). Previews commands to be executed, requires explicit confirmation, displays results in an ASCII table, and logs the operation along with target server connection.


---

## Installation

1. Create the MySQL Shell plugins folder if it doesn't already exist:
   ```bash
   mkdir -p ~/.mysqlsh/plugins
   ```

2. Clone or copy the `user` plugin folder into the plugins directory:
   ```bash
   # Your plugin path must be:
   git clone https://github.com/umer-r/mysqlsh-plugins.git ~/.mysqlsh/plugins/
   ```

3. Start MySQL Shell. The plugin will be automatically discovered and loaded under the `user` namespace.

---

## Usage

Start MySQL Shell and connect to a database instance. Run the functions from the `user` namespace:

### 1. Create a User
Starts an interactive wizard to prompt you for user configuration.
```python
# Starts the interactive configuration wizard
PY > user.create()
```

### 2. Show Grants
View grants for any user account across single or multiple hosts.
```python
# View grants across all hosts for 'developer'
PY > user.show_grants("developer")

# View grants for a specific host
PY > user.show_grants("developer@127.0.0.1")
```

### 3. Sync Grants
Sync permissions from one user to another (supports automatic host resolution if host is omitted).
```python
# Sync grants from 'dev_template' to 'new_developer'
PY > user.sync_grants({origin_user: "dev_template", destination_user: "new_developer"})
```

### 4. Delete User
Safely remove user accounts with a confirmation prompt and summary of target hosts.
```python
# Delete 'obsolete_user' across all hosts
PY > user.delete("obsolete_user")

# Delete a specific account
PY > user.delete("obsolete_user@%")
```

### 5. Rotate Password
Safely rotate user account passwords with a preview of commands, confirmation prompt, and server audit logging.
```python
# Starts the interactive wizard (prompts for username, password, host)
PY > user.rotate_pass()

# Or specify user upfront
PY > user.rotate_pass("developer@localhost")
```

---

## Logging and Auditing

Any write action (`create`, `sync_grants`, `delete`, `rotate_pass`) is appended to a centralized audit log file at:
```bash
~/.mysqlsh/plugins/user/logs/user_plugin.log
```

