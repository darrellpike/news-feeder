from django.core.management.base import BaseCommand
from posts.models import *
import string
import random

class Command(BaseCommand):
    """ This is used for testing, not on the production site. """
    help = "Whatever you want to print here"

    def handle(self, *args, **options):
        for i in range(1000):
            u=User(username=random_string(),password=random_string())
            u.save()

def random_string(size=10, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))
