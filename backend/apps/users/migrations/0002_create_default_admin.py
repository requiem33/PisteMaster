from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_admin(apps, schema_editor):
    User = apps.get_model('users', 'User')
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            password=make_password('admin'),
            role='ADMIN',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_admin),
    ]