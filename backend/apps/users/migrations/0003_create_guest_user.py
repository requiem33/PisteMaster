# Generated data migration for Guest user
# This migration creates the default Guest user for desktop app

from django.db import migrations


def create_guest_user(apps, schema_editor):
    """
    Create the default Guest user.
    This user is used for unauthenticated tournament creation in the desktop app.
    """
    User = apps.get_model("users", "User")
    
    # Check if Guest user already exists
    if User.objects.filter(username="Guest").exists():
        return
    
    User.objects.create(
        username="Guest",
        role="GUEST",
        is_active=True,
        first_name="Guest",
        last_name="User",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_create_default_admin"),
    ]

    operations = [
        migrations.RunPython(create_guest_user),
    ]