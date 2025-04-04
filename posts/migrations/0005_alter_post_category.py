# Generated by Django 5.1.4 on 2025-03-06 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0004_alter_post_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="category",
            field=models.CharField(
                choices=[("service", "Service"), ("rent", "Rent")],
                help_text="Select the category for the post.",
                max_length=15,
                verbose_name="Category",
            ),
        ),
    ]
