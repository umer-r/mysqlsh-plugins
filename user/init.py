"""
user plugin for MySQL Shell — init.py

This file is the plugin entry point. Its only job is to:
  1. Declare the @plugin class so MySQL Shell registers the namespace.
  2. Import every command module so their @plugin_function decorators fire.

To add a new command:
  1. Create commands/<your_command>.py with a @plugin_function("user.<name>").
  2. Add one import line below — that's it.
"""
import sys
import os

# MySQL Shell's embedded Python does not add the plugin directory to sys.path.
# Insert it so that the 'commands' and 'lib' sub-packages are importable.
_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

from mysqlsh.plugin_manager import plugin


@plugin
class user:
    """
    User account management plugin for creating, inspecting, and syncing
    MySQL user grants.
    """


# ── Register commands ────────────────────────────────────────────────────────
# Each import triggers the @plugin_function decorator in that module.

from commands.create import create           # noqa: F401, E402
from commands.show_grants import show_grants # noqa: F401, E402
from commands.sync_grants import sync_grants # noqa: F401, E402
from commands.delete import delete           # noqa: F401, E402
from commands.rotate_pass import rotate_pass # noqa: F401, E402


