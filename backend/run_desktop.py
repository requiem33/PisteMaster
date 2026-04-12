"""
Entry point for desktop application (bundled with PyInstaller)

This script starts the Django development server with desktop settings,
using SQLite in the user data directory.

Usage:
    python run_desktop.py

When bundled with PyInstaller:
    pistemaster-backend.exe
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PisteMaster.settings.desktop")


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    app_name = "PisteMaster"
    home = Path.home()

    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = home / "Library" / "Application Support"
    else:
        base = home / ".local" / "share"

    data_dir = base / app_name / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_base_dir():
    """Get the base directory for Django project."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).parent
    else:
        return Path(__file__).resolve().parent.parent


def main():
    ensure_data_dir()

    base_dir = get_base_dir()
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    port = int(os.environ.get("DJANGO_PORT", 8000))

    print("Starting PisteMaster backend server...")
    print(f"Settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"Data directory: {ensure_data_dir()}")
    print(f"Server: http://127.0.0.1:{port}")

    os.chdir(base_dir)

    from django.core.management import execute_from_command_line

    print("Applying database migrations...")
    execute_from_command_line(["manage.py", "migrate", "--noinput"])
    print("Migrations completed.")

    # Check if Guest user exists
    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        guest_user = User.objects.filter(username="Guest").first()
        if guest_user:
            print(f"Guest user found: {guest_user.username} (role: {guest_user.role})")
        else:
            print("WARNING: Guest user not found after migrations")
    except Exception as e:
        print(f"Error checking Guest user: {e}")

    execute_from_command_line(["manage.py", "runserver", f"127.0.0.1:{port}", "--noreload", "--nothreading"])


if __name__ == "__main__":
    main()
