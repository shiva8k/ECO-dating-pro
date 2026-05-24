from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_notification"),
    ]

    operations = [
        migrations.RenameField(
            model_name="notification",
            old_name="actor",
            new_name="sender",
        ),
        migrations.RenameField(
            model_name="notification",
            old_name="created_at",
            new_name="timestamp",
        ),
    ]
