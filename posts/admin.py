from django.contrib import admin
from posts.models import *
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from solo.admin import SingletonModelAdmin

admin.site.register(User)

feedlyConfig = FeedlyAPISettings.get_solo()

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'post_count', 'comment_count', 'postvote_count', 'commentvote_count', 'is_fake')
    #def has_add_permission(self, request):
    #    return False

admin.site.register(UserProfile, UserProfileAdmin)

class PostAdmin(admin.ModelAdmin):
    list_display = ('title','submit_time', 'url')

admin.site.register(Post, PostAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'text')
    def has_add_permission(self, request):
        return False

class NewsSuggestionsAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'url']

class NewsAggregatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'url',)
    search_fields = ['name', 'url']


class FeedlyAPISettingsAdmin(SingletonModelAdmin):
    readonly_fields = ('api_requests_remained',)

admin.site.register(FeedlyAPISettings, FeedlyAPISettingsAdmin)
admin.site.register(UserNewsSuggestion, NewsSuggestionsAdmin)
admin.site.register(NewsAggregator, NewsAggregatorAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(PostVote)
admin.site.register(CommentVote)
admin.site.register(PostFlag)
# admin.site.register(RelatedArticle)