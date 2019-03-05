from posts.models import *

"""
from configstore.configs import get_config
config = get_config('Top Counter')
tagline_config = get_config('Tagline')
karma_threshold_config = get_config('Karma Threshold')

def config_settings(request):
    return {'settings_post_count':config.get('posts',400)+Post.objects.all().count(),
            'settings_comment_count':config.get('comments',600)+Comment.objects.all().count(),
            'settings_member_count':config.get('members',200)+User.objects.all().count(),
            'title_tagline':tagline_config.get('text',"A community."),
            'karma_threshold':karma_threshold_config.get('karma_threshold',0),
            }
"""
#This used to use the configstore module, but I couldn't get that working again (probably doesn't work with Django 1.9),
#so I just define the terms manually for now.
def config_settings(request):
    return {'settings_post_count':Post.objects.all().count(),
            'settings_comment_count':Comment.objects.all().count(),
            'settings_member_count':User.objects.all().count(),
            'title_tagline':"A community.",
            'karma_threshold':0
    }
