# Generated by Django 5.1.4 on 2025-04-12 05:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0007_category_description_category_icon_class"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Category",
            new_name="ItemCategory",
        ),
    ]
