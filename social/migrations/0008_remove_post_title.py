# Generated by Django 5.0.6 on 2024-10-09 15:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0007_post_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='title',
        ),
    ]
