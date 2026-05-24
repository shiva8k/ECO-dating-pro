from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_rename_notification_fields"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="notification",
            options={"ordering": ["-timestamp"]},
        ),
    ]
