from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelForm
from django.forms import TextInput, Textarea
from posts.models import *
from django_registration.forms import RegistrationFormUniqueEmail
from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import ugettext_lazy as _
from posts.utils import update_contact_property_hubspot
from django.forms import ValidationError
from django.contrib.auth import password_validation
from django.core.validators import EmailValidator, validate_image_file_extension
from django.core.files.images import get_image_dimensions
from social_django.models import UserSocialAuth

User = get_user_model()


class UserProfileUpdateForm(ModelForm):
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autofocus': True}),
        required=False
    )
    new_password = forms.CharField(
        label=_("New password"),
        strip=False,
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
        required=False
    )
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.CharField(required=False, validators=[EmailValidator])

    def clean(self):
        cleaned_data = self.cleaned_data
        for field in cleaned_data:
            if self.cleaned_data[field] == '' and field not in ['old_password', 'new_password']:
                self.cleaned_data[field] = getattr(self.instance, field)
        return self.cleaned_data

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            response = update_contact_property_hubspot(self.instance.email, 'firstname', first_name)
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            response = update_contact_property_hubspot(self.instance.email, 'lastname', last_name)
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            if user.pk == self.instance.pk:
                return email
        except User.DoesNotExist:
            if email:
                response = update_contact_property_hubspot(self.instance.email, 'email', email)

            return email
        raise ValidationError(_('This email address is already in use. Please supply a different email address.'),
                              code='email_already_exists')


    def clean_new_password(self):
        """
        Validate that the old_password field is exists
        """
        old_password = self.cleaned_data.get('old_password')
        new_password = self.cleaned_data.get('new_password')
        if new_password and not old_password and not self.instance.check_password(old_password):
            raise forms.ValidationError('Please enter your old password.', code='password_incorrect')
        return new_password

    def clean_old_password(self):
        """
        Validate that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if old_password and not self.instance.check_password(old_password):
            raise forms.ValidationError(
                "Incorrect password.",
                code='password_incorrect',
            )
        return old_password

    def save(self, commit=True):
        """Save the new password."""
        instance = super().save()
        password = self.cleaned_data["new_password"]
        if password:
            instance.set_password(password)
        if commit:
            instance.save()
        return instance

    class Meta:
        model = User
        fields = [User.USERNAME_FIELD, 'first_name', 'last_name', 'email', 'old_password', 'new_password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['userprofile_defined_code'] = forms.ModelChoiceField(queryset=UserProfile.objects.filter(user=kwargs.get('instance')))

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

class NewCommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text',]
        widgets = {
            'text': Textarea(attrs={'class': 'form-control col-md-12 comment-form',
                                    'rows':'4',
                                    'placeholder':'write a comment...',}),
            }


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
            'username',
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


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        super().send_mail(subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None)
        url = '%s://%s/accounts/reset/%s/%s/' % (context['protocol'], context['domain'], context['uid'], context['token'])
        response =  update_contact_property_hubspot(to_email, 'password_reset_url_active', True,
                                        options=[{'label': 'Yes', 'value': True},
                                                    {'label': 'No', 'value': False}])
        if response == 404:
            raise ValidationError("User doesn't exist on HubSpot")
        r = update_contact_property_hubspot(to_email, 'password_reset_url', url)



    def clean_email(self):
        email = self.cleaned_data['email']
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            try:
                UserSocialAuth.objects.get(user_id=user.id)
            except UserSocialAuth.DoesNotExist:
                return email
        except User.DoesNotExist:
            raise ValidationError(
                _('User with this email doesn\'t exist.'),
                code='invalid'
            )
        raise ValidationError(_('User with this email was logged in via LinkedIn'), code='invalid')



class ChangeUserImageForm(forms.Form):
    """Profile image upload form."""
    new_image = forms.ImageField(validators=[validate_image_file_extension])

    def clean_new_image(self):
        new_image = self.cleaned_data.get('new_image')
        if not new_image:
            raise forms.ValidationError("No image!")
        else:
            w, h = get_image_dimensions(new_image)
            if w < 110:
                raise forms.ValidationError("The image is %i pixel wide. It's supposed to be more than 110px" % w)
            if h < 110:
                raise forms.ValidationError("The image is %i pixel high. It's supposed to be more than 110px" % h)
            return new_image


class NewNewsSuggestionForm(ModelForm):

    def clean_url(self):
        url = self.cleaned_data.get('url')
        try:
            UserNewsSuggestion.objects.get(url=url)
            raise ValidationError(_('This link has already been suggested!'), code='url_already_exists')
        except UserNewsSuggestion.DoesNotExist:
            return url
        except UserNewsSuggestion.MultipleObjectsReturned:
            raise ValidationError(_('This link has already been suggested!'), code='url_already_exists')

    class Meta:
        model = UserNewsSuggestion
        fields = ['url',]
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
