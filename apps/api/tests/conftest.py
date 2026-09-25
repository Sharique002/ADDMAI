"""Pytest fixtures for ADDMAI API tests."""

import os
import sys
from pathlib import Path

# Ensure apps/api is on sys.path
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Set test environment
os.environ["APP_ENV"] = "testing"
