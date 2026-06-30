"""
Shared pytest configuration for server/tests/.
Sets up sys.path once here — test files do NOT need their own sys.path.insert.
"""

import sys
import os

# Single path setup for all test files
_server_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "server"))
if _server_path not in sys.path:
    sys.path.insert(0, _server_path)
