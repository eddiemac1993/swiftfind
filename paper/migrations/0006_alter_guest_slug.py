# Generated by Django 5.1.4 on 2025-03-21 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("paper", "0005_guest_created_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="guest",
            name="slug",
            field=models.SlugField(unique=True),
        ),
    ]
