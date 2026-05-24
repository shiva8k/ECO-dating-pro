from django.db import migrations, models


def mark_existing_profiles_complete(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")
    for profile in Profile.objects.all():
        if profile.college_name or profile.bio or profile.profile_picture:
            profile.onboarding_completed = True
            profile.save(update_fields=["onboarding_completed"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_create_default_premium_plan"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="age",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[
                    ("male", "Male"),
                    ("female", "Female"),
                    ("non_binary", "Non-binary"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="interested_in",
            field=models.CharField(
                blank=True,
                choices=[
                    ("male", "Male"),
                    ("female", "Female"),
                    ("everyone", "Everyone"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="looking_for",
            field=models.CharField(
                blank=True,
                choices=[
                    ("friendship", "Friendship"),
                    ("relationship", "Relationship"),
                    ("situationship", "Situationship"),
                    ("study_partner", "Study Partner"),
                    ("networking", "Networking"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="onboarding_completed",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="profile",
            name="interests",
            field=models.CharField(
                blank=True,
                help_text="Comma-separated interest slugs, e.g. coding,gaming,travel.",
                max_length=255,
            ),
        ),
        migrations.RunPython(mark_existing_profiles_complete, migrations.RunPython.noop),
    ]
