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


def ensure_guest_user():
    """Ensure Guest user exists with correct password 'Guest'."""
    from django.contrib.auth import get_user_model
    from django.contrib.auth.hashers import make_password, check_password

    User = get_user_model()

    # Get or create Guest user
    guest_user, created = User.objects.get_or_create(
        username="Guest",
        defaults={
            "role": "GUEST",
            "is_active": True,
            "first_name": "Guest",
            "last_name": "User",
            "password": make_password("Guest"),
        },
    )

    if created:
        print("Created Guest user with password 'Guest'")
    else:
        # Check if password needs update
        if not check_password("Guest", guest_user.password):
            guest_user.password = make_password("Guest")
            guest_user.save()
            print("Updated Guest user password to 'Guest'")
        else:
            print("Guest user password verified")

    return guest_user


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

    # Ensure Guest user exists with correct password
    try:
        _guest_user = ensure_guest_user()  # noqa: F841

        # Test authentication
        from django.contrib.auth import authenticate

        user = authenticate(username="Guest", password="Guest")
        if user:
            print("Guest authentication test: SUCCESS")
        else:
            print("Guest authentication test: FAILED - check password hash")
    except Exception as e:
        print(f"Error ensuring Guest user: {e}")

    execute_from_command_line(["manage.py", "runserver", f"127.0.0.1:{port}", "--noreload", "--nothreading"])


if __name__ == "__main__":
    main()
