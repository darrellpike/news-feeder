from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import imagekit.models.fields
import mptt.fields


class Migration(migrations.Migration):
	dependencies = [
		('posts', '0001_initial'),
	]
	operations = [
		migrations.CreateModel(
			name='NewsAggregator',
			fields=[
				('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('name', models.CharField(max_length=85)),
				('url', models.URLField(max_length=85)),
				('logo', imagekit.models.fields.ProcessedImageField(null=True, upload_to='news_site_logos/')),
			],
		),
	]