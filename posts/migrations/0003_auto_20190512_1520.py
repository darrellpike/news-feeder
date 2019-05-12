# Generated by Django 2.2 on 2019-05-12 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_custom'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='hubspot_contact',
            field=models.CharField(blank=True, max_length=85),
        ),
        migrations.AlterField(
            model_name='post',
            name='label_for_url',
            field=models.CharField(blank=True, help_text="If post don't have news_aggregator, this label will replace news aggregator name", max_length=85),
        ),
    ]
