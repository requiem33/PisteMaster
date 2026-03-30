# Generated migration to set created_by for existing tournaments

from django.db import migrations


def set_created_by_for_existing_tournaments(apps, schema_editor):
    """
    Set created_by to thefirst admin user for existing tournaments.
    This ensures all pre-existing tournaments have an owner.
    """
    DjangoTournament = apps.get_model('fencing_organizer', 'DjangoTournament')
    User = apps.get_model('users', 'User')
    
    # Get the first admin user
    admin_user = User.objects.filter(role='ADMIN').first()
    
    if admin_user:
        # Update all tournaments with no creator
        DjangoTournament.objects.filter(created_by__isnull=True).update(created_by=admin_user)


class Migration(migrations.Migration):

    dependencies = [
        ("fencing_organizer", "0017_tournament_user_fields"),
        ("users", "0002_create_default_admin"),
    ]

    operations = [
        migrations.RunPython(
            set_created_by_for_existing_tournaments,
            reverse_code=migrations.RunPython.noop,
        ),
    ]