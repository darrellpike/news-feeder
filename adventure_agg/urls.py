from django.conf.urls import patterns, include, url
from posts import views, forms
import django.contrib.auth.views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


from registration.backends.simple.views import RegistrationView as SimpleRegistrationView
class RegistrationView(SimpleRegistrationView):
    def get_success_url(self, user):
        return ("/", (), {})

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^ask/$', views.index_ask, name='index_ask'),
    url(r'^new/$', views.index_new, name='index_new'),
    url(r'^popular/$', views.index_popular, name='index_popular'),
    url(r'^most_comments/$', views.index_most_comments, name='index_most_comments'),
    url(r'^vegan/$', views.index_vegan, name='index_vegan'),
    
    url(r'^search/$', views.search, name='search'),
    
    url(r'^admin_dashboard/$', views.admin_scheduled_posts, name='admin_dashboard'),
    url(r'^admin_dashboard/scheduled_posts/$', views.admin_scheduled_posts, name='admin_scheduled_posts'),
    url(r'^admin_dashboard/stats_and_analytics/$', views.admin_stats_and_analytics, name='admin_stats_and_analytics'),
    url(r'^admin_dashboard/buffer_profiles/$', views.admin_buffer_profiles, name='admin_buffer_profiles'),
    url(r'^admin_dashboard/active_users/$', views.admin_active_users, name='admin_active_users'),
    
    url(r'^admin_submit_post/$', views.admin_submit_post, name='admin_submit_post'),
    
    url(r'^email_share/$', views.email_share, name='email_share'),
    
    url(r'^fetch_instagram_images/$', views.fetch_instagram_images, name='fetch_instagram_images'),
    
    url(r'^about/$', views.about, name='about'),
    url(r'^guidelines/$', views.guidelines, name='guidelines'),

    url(r'^vote_post/$', views.vote_post, name='vote_post'),
    url(r'^vote_comment/$', views.vote_comment, name='vote_comment'),
    
    url(r'^post/(?P<post_id>\d+)/$', views.view_post, name='view_post'),
    url(r'^post/(?P<post_id>\d+)/share_now/$', views.share_now, name='share_now'),
    url(r'^post/(?P<post_id>\d+)/comment/(?P<comment_id>\d+)/$', views.view_comment, name='view_comment'),
    url(r'^post/(?P<post_id>\d+)/comment/(?P<comment_id>\d+)/edit$', views.edit_comment, name='edit_comment'),
    
    url(r'^post/(?P<post_id>\d+)/reply$', views.add_comment, name='add_comment'),
    url(r'^post/(?P<post_id>\d+)/flag_post$', views.flag_post, name='flag_post'),
    url(r'^post/(?P<post_id>\d+)/comment/(?P<parent_id>\d+)/reply$', views.add_comment, name='add_comment'),
    
    url(r'^user/(?P<user_id>\d+)/$', views.view_profile, name='view_profile'),
    url(r'^user/(?P<user_id>\d+)/submissions/$', views.view_user_submissions, name='view_user_submissions'),
    url(r'^user/(?P<user_id>\d+)/comments/$', views.view_user_comments, name='view_user_comments'),
    
    url(r'^submit/$', views.submit_post, name='submit_post'),
    
    url(r'^register/$', RegistrationView.as_view(form_class=forms.CustomRegistrationForm), name='registration_register'),
    url(r'^', include('registration.backends.simple.urls')), 
    
    url(r'^staff_delete/img/(?P<image_id>\d+)/$', views.admin_delete_image, name='admin_delete_image'),
    
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
    
    url(r'^admin/', include(admin.site.urls)),
]

#for static files on heroku
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
