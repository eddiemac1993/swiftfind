# Generated by Django 5.2.1 on 2025-05-18 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "directory",
            "0013_alter_businessimage_options_businessimage_is_primary_and_more",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="businessimage",
            options={},
        ),
        migrations.RemoveField(
            model_name="businessimage",
            name="is_primary",
        ),
        migrations.AlterField(
            model_name="business",
            name="slug",
            field=models.SlugField(blank=True),
        ),
        migrations.AlterField(
            model_name="businessimage",
            name="image",
            field=models.ImageField(
                blank=True, null=True, upload_to="business_images/"
            ),
        ),
        migrations.DeleteModel(
            name="BusinessPostGalleryImage",
        ),
    ]
