from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelForm
from django.forms import TextInput, Textarea
from posts.models import *
from django_registration.forms import RegistrationFormUniqueEmail
from django.utils.translation import ugettext_lazy as _
# from .utils import *

User = get_user_model()

class PartialPostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title','url','text']
        widgets = {
            'text': Textarea(attrs={'class': 'form-control col-lg-8 text-input',
                                    'rows':'4'}),
            'url': TextInput(attrs={'class': 'form-control col-lg-8 text-input',
                                    }),
            'title': TextInput(attrs={'class': 'form-control col-lg-8 text-input',
                                    }),
            }
        #def clean_text(self):
        #url = self.cleaned_data.get('url', '')
        #text = self.cleaned_data['text']
        #if not (url or text):
        #    raise forms.ValidationError("You must include a url or text.")
        #return text

class PartialCommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text',]
        widgets = {
            'text': Textarea(attrs={'class': 'form-control col-md-12 comment-form',
                                    'rows':'4',
                                    'placeholder':'write a comment...',}),
            }


class PartialUserProfileForm(ModelForm):
    email = forms.EmailField(widget=TextInput(attrs={'class':'span3'}))
#    description = forms.CharField(required=False, max_length=500)
#    is_email_public = forms.BooleanField(required=False)

    class Meta:
        model = UserProfile
        fields = ('email', 'description', 'is_email_public')
        widgets = {
            'description': Textarea(attrs={'class': 'span3',
                                           'rows':'4'})
            }

    def clean_email(self):
        user = self.instance.user
        user.email = self.cleaned_data["email"]
        user.save()
        return user.email


class CustomRegistrationForm(RegistrationFormUniqueEmail):
    """
    Subclass of ``RegistrationForm`` which enforces uniqueness of
    email addresses.
    
    """
    password2 = None
    class Meta(RegistrationFormUniqueEmail.Meta):
        model = User
        fields = [
            User.USERNAME_FIELD,
            'first_name',
            'last_name',
            'password1',
        ]
        required_css_class = 'required'


class PostVoteForm(ModelForm):
    class Meta:
        fields = ('post',)
        model = PostVote


class CommentVoteForm(ModelForm):
    class Meta:
        fields = ('score', 'comment')
        model = CommentVote

# class BufferProfileForm(ModelForm):
#     class Meta:
#         model=BufferProfile
#         exclude = []
"""
from configstore.configs import ConfigurationInstance, register
from configstore.forms import ConfigurationForm

class TopCounterConfigurationForm(ConfigurationForm):
    posts = forms.IntegerField()
    members = forms.IntegerField()
    comments = forms.IntegerField()

topcounter_instance = ConfigurationInstance('Top Counter', 'Top Count Config', TopCounterConfigurationForm)
register(topcounter_instance)

class AboutConfigurationForm(ConfigurationForm):
    text = forms.CharField(widget=forms.Textarea)

about_instance = ConfigurationInstance('About Page', 'About Page Config', AboutConfigurationForm)
register(about_instance)

class GuidelinesConfigurationForm(ConfigurationForm):
    text = forms.CharField(widget=forms.Textarea)

guidelines_instance = ConfigurationInstance('Guidelines Page', 'Guidelines Page Config', GuidelinesConfigurationForm)
register(guidelines_instance)


class TaglineConfigurationForm(ConfigurationForm):
    text = forms.CharField(widget=forms.Textarea)

tagline_instance = ConfigurationInstance('Tagline', 'Tagline Config', TaglineConfigurationForm)
register(tagline_instance)

class KarmaThresholdConfigurationForm(ConfigurationForm):
    karma_threshold = forms.IntegerField()

karmathreshold_instance = ConfigurationInstance('Karma Threshold', 'Karma Threshold Config', KarmaThresholdConfigurationForm)
register(karmathreshold_instance)

"""
