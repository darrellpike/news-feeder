from django.core.management.base import BaseCommand
from posts.models import *
import string
import random

class Command(BaseCommand):
    """ This is used for testing, not on the production site. """
    help = "Whatever you want to print here"

    def handle(self, *args, **options):
        for i in range(200):
            rand_user=random.choice(User.objects.all())
            rand_post=random.choice(Post.objects.all())
            while rand_post.user_voted(rand_user):
                rand_post=random.choice(Post.objects.all())
            v=PostVote(voter=rand_user,post=rand_post,score=random.choice(['1','-1']))
            v.save()

def random_string(size=10, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

