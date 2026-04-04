# Data migration to fix Guest user password
# This migration ensures the Guest user has a properly hashed password

from django.db import migrations
from django.contrib.auth.hashers import make_password


def set_guest_password(apps, schema_editor):
    """
    Set the password for the Guest user.
    This migration is idempotent - it handles both existing and missing Guest users.
    """
    User = apps.get_model("users", "User")
    
    # Try to get existing Guest user
    try:
        guest_user = User.objects.get(username="Guest")
        # Update password for existing user
        guest_user.password = make_password("Guest")
        guest_user.save()
    except User.DoesNotExist:
        # Create Guest user with password if it doesn't exist
        User.objects.create(
            username="Guest",
            password=make_password("Guest"),
            role="GUEST",
            is_active=True,
            first_name="Guest",
            last_name="User",
        )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_create_guest_user"),
    ]

    operations = [
        migrations.RunPython(set_guest_password),
    ]