from django.core.management.base import BaseCommand
from posts.models import *
from posts.utils import *
import string
import random
from operator import attrgetter
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):

    help = "Whatever you want to print here"

    def handle(self, *args, **options):
        interval = timedelta(days=1)
        now = timezone.now()
        InstagramImage.objects.filter(created_time__lt=now-interval).delete()
