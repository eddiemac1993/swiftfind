# Generated by Django 5.1.4 on 2025-04-24 13:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("directory", "0008_business_company_profile_product_service"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="service",
            name="business",
        ),
        migrations.DeleteModel(
            name="Product",
        ),
        migrations.DeleteModel(
            name="Service",
        ),
    ]
