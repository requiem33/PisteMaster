"""
pytest configuration for PisteMaster project.
Configures Django settings and Python paths for testing.
"""

import sys
from pathlib import Path

# Add project root and backend to Python path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))