# Generated by Django 3.0.7 on 2020-06-28 18:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homes', '0003_auto_20200628_1711'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='match',
            name='updated_at',
        ),
    ]