# Generated by Django 5.1.2 on 2024-10-31 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_apikey'),
    ]

    operations = [
        migrations.AddField(
            model_name='authuser',
            name='auth_provider',
            field=models.CharField(default='email', max_length=20),
        ),
    ]
