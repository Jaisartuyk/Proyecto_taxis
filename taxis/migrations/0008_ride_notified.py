# Generated by Django 5.1.4 on 2025-01-29 03:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taxis", "0007_remove_ride_destination_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="ride",
            name="notified",
            field=models.BooleanField(default=False),
        ),
    ]
