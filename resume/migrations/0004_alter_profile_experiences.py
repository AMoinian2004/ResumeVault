# Generated by Django 5.1 on 2024-09-14 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resume', '0003_profile_experiences_profile_graduation_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='experiences',
            field=models.JSONField(blank=True),
        ),
    ]
