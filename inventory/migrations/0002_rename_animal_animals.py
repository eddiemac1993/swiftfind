# Generated by Django 5.1.4 on 2025-02-04 08:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Animal",
            new_name="Animals",
        ),
    ]
