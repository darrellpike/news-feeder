from django.core.management.base import BaseCommand
from posts.models import *
from posts.util import *
import string
import random
from operator import attrgetter

class Command(BaseCommand):

    help = "Whatever you want to print here"

    def handle(self, *args, **options):
        tags = InstagramHashtagsToFetch.objects.all()
        for tag in tags:
            tag = tag.tag
            results = get_instagram_images(tag, 33)
            results=sorted(results,key=attrgetter('comments', 'likes'), reverse=True)
            for r in results[:3]:
                image_info, comments = parse_instagram_to_dic(r)
                image_info['tag']=tag
                image, created = InstagramImage.objects.get_or_create(instagram_id=r.id, defaults=image_info)
                if not created:
                    InstagramImage.objects.filter(pk=image.pk).update(**image_info)
                for c in comments:
                    c['image']=image
                    comment, comment_created = InstagramComment.objects.get_or_create(instagram_id=c['instagram_id'], defaults=c)
                    if not comment_created:
                        InstagramComment.objects.filter(pk=comment.pk).update(**c)
