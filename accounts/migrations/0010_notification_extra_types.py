from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_profile_onboarding_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("like", "Like"),
                    ("match", "Match"),
                    ("message", "Message"),
                    ("profile_view", "Profile View"),
                    ("premium", "Premium"),
                ],
                max_length=20,
            ),
        ),
    ]
