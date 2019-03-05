from django.core.management.base import BaseCommand
from posts.models import *
from posts.util import *
import string
import random
from operator import attrgetter
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):

    help = "Whatever you want to print here"

    def handle(self, *args, **options):
        interval = timedelta(hours=4)
        now = timezone.now()
        images = InstagramImage.objects.filter(created_time__gt=now-interval)
        for image in images:
            print image.pk
            print image.instagram_id
            image.refetch_info()
