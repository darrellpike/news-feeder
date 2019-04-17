from django.conf.urls import patterns, include, url
from posts import old_views, forms, views
import django.contrib.auth.views
from django.conf import settings
from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


from registration.backends.simple.views import RegistrationView as SimpleRegistrationView
class RegistrationView(SimpleRegistrationView):
    def get_success_url(self, user):
        return ("/", (), {})

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^latest/$', views.IndexLatestView.as_view(), name='index_latest'),
    url(r'^ask/$', old_views.index_ask, name='index_ask'),
    url(r'^new/$', old_views.index_new, name='index_new'),
    url(r'^popular/$', old_views.index_popular, name='index_popular'),
    url(r'^most_comments/$', old_views.index_most_comments, name='index_most_comments'),
    url(r'^vegan/$', old_views.index_vegan, name='index_vegan'),
    
    url(r'^search/$', old_views.search, name='search'),
    
    url(r'^admin_dashboard/$', old_views.admin_scheduled_posts, name='admin_dashboard'),
    url(r'^admin_dashboard/scheduled_posts/$', old_views.admin_scheduled_posts, name='admin_scheduled_posts'),
    url(r'^admin_dashboard/stats_and_analytics/$', old_views.admin_stats_and_analytics, name='admin_stats_and_analytics'),
    url(r'^admin_dashboard/buffer_profiles/$', old_views.admin_buffer_profiles, name='admin_buffer_profiles'),
    url(r'^admin_dashboard/active_users/$', old_views.admin_active_users, name='admin_active_users'),
    
    url(r'^admin_submit_post/$', old_views.admin_submit_post, name='admin_submit_post'),
    
    url(r'^email_share/$', old_views.email_share, name='email_share'),
    
    url(r'^fetch_instagram_images/$', old_views.fetch_instagram_images, name='fetch_instagram_images'),
    
    url(r'^about/$', old_views.about, name='about'),
    url(r'^guidelines/$', old_views.guidelines, name='guidelines'),

    url(r'^vote_post/$', views.vote_post, name='vote_post'),
    url(r'^vote_comment/$', old_views.vote_comment, name='vote_comment'),
    
    url(r'^post/(?P<pk>\d+)/$', views.PostDetailView.as_view(), name='view_post'),
    url(r'^post/(?P<post_id>\d+)/share_now/$', old_views.share_now, name='share_now'),
    url(r'^post/(?P<post_id>\d+)/comment/(?P<comment_id>\d+)/$', old_views.view_comment, name='view_comment'),
    url(r'^post/(?P<post_id>\d+)/comment/(?P<comment_id>\d+)/edit$', old_views.edit_comment, name='edit_comment'),
    
    url(r'^post/(?P<post_id>\d+)/reply$', old_views.add_comment, name='add_comment'),
    url(r'^post/(?P<post_id>\d+)/flag_post$', old_views.flag_post, name='flag_post'),
    url(r'^post/(?P<post_id>\d+)/comment/(?P<parent_id>\d+)/reply$', old_views.add_comment, name='add_comment'),
    
    url(r'^user/(?P<user_id>\d+)/$', old_views.view_profile, name='view_profile'),
    url(r'^user/(?P<user_id>\d+)/submissions/$', old_views.view_user_submissions, name='view_user_submissions'),
    url(r'^user/(?P<user_id>\d+)/comments/$', old_views.view_user_comments, name='view_user_comments'),
    
    url(r'^submit/$', old_views.submit_post, name='submit_post'),
    
    url(r'^register/$', RegistrationView.as_view(form_class=forms.CustomRegistrationForm), name='registration_register'),
    url(r'^', include('registration.backends.simple.urls')), 
    
    url(r'^staff_delete/img/(?P<image_id>\d+)/$', old_views.admin_delete_image, name='admin_delete_image'),
    
    url(r'^forgot_password/$', 
        django.contrib.auth.views.password_reset, 
        {'post_reset_redirect' : '/forgot_password/done/'},
        name="password_reset"),
    url(r'^forgot_password/done/$',
        django.contrib.auth.views.password_reset_done),
    url(r'^password_reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 
        django.contrib.auth.views.password_reset_confirm,
        {'post_reset_redirect' : '/password_reset/done/'}),
    url(r'^password_reset/done/$', 
        django.contrib.auth.views.password_reset_complete),
    
    url(r'^WHN@dm!n/', include(admin.site.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#for static files on heroku
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
