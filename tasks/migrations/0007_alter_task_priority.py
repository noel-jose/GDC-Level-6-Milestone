# Generated by Django 4.0.1 on 2022-01-29 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_alter_task_priority'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='priority',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
