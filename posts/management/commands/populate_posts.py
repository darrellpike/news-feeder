from django.core.management.base import BaseCommand
from posts.models import *
import string
import random

class Command(BaseCommand):
    """ This is used for testing, not on the production site. """
    help = "Whatever you want to print here"

    #option_list = NoArgsCommand.option_list + (
    #    make_option('--verbose', action='store_true'),
    #)

    def handle(self, *args, **options):
        for i in range(200):
            rand_user=random.choice(User.objects.all())
            p=Post(submitter=rand_user,title=random_string(size=20),text=random_string(400))
            p.save()

def random_string(size=10, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

