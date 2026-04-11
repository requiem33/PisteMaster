from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cluster", "0005_add_master_latest_sync_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="djangoclusterconfig",
            name="master_port",
            field=models.IntegerField(blank=True, default=8000, null=True, verbose_name="Master Port"),
        ),
    ]