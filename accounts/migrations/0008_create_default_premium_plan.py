from django.db import migrations


def create_default_premium_plan(apps, schema_editor):
    PremiumPlan = apps.get_model("accounts", "PremiumPlan")
    PremiumPlan.objects.get_or_create(
        slug="monthly-premium",
        defaults={
            "name": "Monthly Premium",
            "price_inr": 299,
            "duration_days": 30,
            "description": "Monthly ECO Premium with unlimited likes, who-liked-you, boost, and badge.",
            "is_active": True,
        },
    )


def remove_default_premium_plan(apps, schema_editor):
    PremiumPlan = apps.get_model("accounts", "PremiumPlan")
    PremiumPlan.objects.filter(slug="monthly-premium").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_premiumplan_paymenthistory_premiumsubscription"),
    ]

    operations = [
        migrations.RunPython(create_default_premium_plan, remove_default_premium_plan),
    ]
