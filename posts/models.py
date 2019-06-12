from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import MaxLengthValidator
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import DatabaseError
# from .utils import *
from django.db.models import Max
import random
import requests
from django.core import signing
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _
from urllib.parse import urlparse
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.conf import settings
from solo.models import SingletonModel
from posts.utils import FeedlyClient

CHAR_FIELD_MAX_LENGTH = 85


REGISTRATION_SALT = getattr(settings, 'REGISTRATION_SALT', 'registration')


class CustomUserManager(BaseUserManager):
	def _create_user(self, email, username, password, **extra_fields):
		"""
		Create and save a user with the given username, email, and password.
		"""
		if not email:
			raise ValueError('The given email must be set')
		if not username:
			raise ValueError('The given username must be set')
		email = self.normalize_email(email)
		username = self.model.normalize_username(username)
		user = self.model(username=username, email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, email, username, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', False)
		extra_fields.setdefault('is_superuser', False)
		return self._create_user(email, username, password, **extra_fields)

	def create_superuser(self, email, username, password, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		extra_fields.setdefault('is_active', True)

		if extra_fields.get('is_staff') is not True:
			raise ValueError('Superuser must have is_staff=True.')
		if extra_fields.get('is_superuser') is not True:
			raise ValueError('Superuser must have is_superuser=True.')

		return self._create_user(email, username, password, **extra_fields)

	def get_by_natural_key(self, email_):
		return self.get(email=email_)



class User(AbstractBaseUser, PermissionsMixin):
	"""
    Here we are subclassing the Django AbstractBaseUser, which comes with only
    3 fields:
    1 - password
    2 - last_login
    3 - is_active
    Note than all fields would be required unless specified otherwise, with
    `required=False` in the parentheses.
    The PermissionsMixin is a model that helps you implement permission settings
    as-is or modified to your requirements.
    More info: https://goo.gl/YNL2ax
    """
	email = models.EmailField(_('email address'), unique=True)
	first_name = models.CharField(_('first name'), max_length=30)
	last_name = models.CharField(_('last name'), max_length=30)
	username = models.CharField(
		_('username'),
		max_length=150,
		unique=True,
		help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
		validators=[UnicodeUsernameValidator()],
		error_messages={
			'unique': _("A user with that username already exists."),
		},
	)
	is_staff = models.BooleanField(default=False)
	date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
	is_active = models.BooleanField(default=False)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username']

	objects = CustomUserManager()

	def get_full_name(self):
		"""
		Returns the first_name plus the last_name, with a space in between.
		"""
		full_name = '%s %s' % (self.first_name, self.last_name)
		return full_name.strip()


	def get_short_name(self):
		return self.username


	def natural_key(self):
		return self.email


	def email_user(self, subject, message, from_email=None, **kwargs):
		"""
		Sends an email to this User. IMPORTANT: Use HubSpot for sending emails.
		"""
		pass


	def get_activation_key(self):
		"""
		Generate the activation key which will be emailed to the user.

		"""
		return signing.dumps(
			obj=self.get_username(),
			salt=REGISTRATION_SALT
		)


	def __str__(self):
		full_name = '%s | %s' % (self.username, self.email)
		return full_name.strip()


class UserProfile(models.Model):
	user = models.OneToOneField(
		User, primary_key=True, editable=False, on_delete=models.CASCADE, related_name='userprofile')
	image = models.ImageField(
		default='user_images/default/default_image_profile.png', upload_to='user_images/', blank=True)
	image_thumbnail_sm = ImageSpecField(source='image',
	                                processors=[ResizeToFill(100,100)],
	                                format='PNG')
	image_thumbnail_md = ImageSpecField(source='image',
	                                processors=[ResizeToFill(300,300)],
	                                format='PNG')
	hubspot_contact = models.BooleanField(default=False)
	description = models.TextField(blank=True, validators=[MaxLengthValidator(500)])
	is_email_public = models.BooleanField(default=False)
	is_shadowbanned = models.BooleanField(default=False)
	is_fake = models.BooleanField(default=False)

	def is_image_default(self):
		return True if self.image.name == 'user_images/default/default_image_profile.png' else False


	def count_karma(self):
		#I know the score-counting would be shorter and faster using a SUM(score) instead of fors, but django
		#seems to have a bug when chaining multiple aggregates.
		posts = Post.objects.filter(submitter=self.user).annotate(score=Sum('postvote__score'))
		total_score = 0
		for p in posts:
			if not p.score is None:
				total_score += p.score
		comments = Comment.objects.filter(author=self.user).annotate(score=Sum('commentvote__score'))
		for c in comments:
			if not c.score is None:
				total_score += c.score
		return total_score

	def __unicode__(self):
		display = self.user.username
		return display

	def post_count(self):
		return self.user.post_set.count()
	def comment_count(self):
		return self.user.comment_set.count()
	def postvote_count(self):
		return self.user.postvote_set.count() - self.post_count()
	def commentvote_count(self):
		return self.user.commentvote_set.count() - self.comment_count()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwarg):
	if created:
		profile = UserProfile(user=instance)
		profile.save()


class NewsAggregator(models.Model):
	name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
	url = models.URLField(max_length=CHAR_FIELD_MAX_LENGTH)
	logo = ProcessedImageField(upload_to='news_site_logos/',
	                                     processors=[ResizeToFit(100,100)],
	                                     format='JPEG',
	                                     null=True)

	def __str__(self):
		return self.name


class Post(models.Model):
	title = models.CharField(max_length=85)
	submitter = models.ForeignKey(User, on_delete=models.CASCADE)
	author = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH, blank=True, null=True)
	submit_time = models.DateTimeField(default=timezone.now)
	news_aggregator = models.ForeignKey('NewsAggregator', on_delete=models.CASCADE, blank=True, null=True)
	url = models.URLField(max_length=300, blank=True)
	label_for_url = models.CharField(max_length=85, blank=True, help_text=_(
		"If post don't have news_aggregator, this label will replace news aggregator name"))
	text = models.TextField(blank=True)
	article_text = models.TextField(blank=True)
	image = models.ImageField(blank=True)
	image_url = models.URLField(blank=True, help_text="If post doesn't have image on the server,"
	                                                  " URL link will be used.")

	def time_since_submit(self):
		return timezone.now() - self.submit_time

	def comment_count(self):
		return Comment.objects.filter(post=self).exclude(author__userprofile__is_shadowbanned=True).count()

	def user_voted(self, user):
		return PostVote.objects.filter(post=self).filter(voter=user).exists()

	def get_score(self):
		score = PostVote.objects.filter(post=self).aggregate(Sum('score'))['score__sum']
		if score is None:
			score=0
		return score

	def get_score_formatted(self):
		score = self.get_score()
		if score >= 10000:
			formatted_number = float(score) / 1000
			formatted_number = str(formatted_number)[:4] + 'k'
			return formatted_number
		else:
			return score

	def get_ranking(self,score=None):
		if score is None:
			score=self.get_score()
		timediff = timezone.now() - self.submit_time
		hours_since = timediff.seconds/60./60 + timediff.days*24.
		return calculate_rank(score,hours_since)

	def __unicode__(self):
		return self.title


def calculate_rank(score,hours_since):
	return (score-.9)# / (hours_since + 2)**1.8


class Comment(MPTTModel):
	author = models.ForeignKey(User, on_delete=models.CASCADE)
	post = models.ForeignKey(Post, editable=False, on_delete=models.CASCADE)
	submit_time = models.DateTimeField(auto_now_add=True)
	text = models.TextField(blank=False)

	parent = TreeForeignKey(
		'self', null=True, blank=True, related_name='children', editable=False, on_delete=models.CASCADE)

	class MPTTMeta:
		# comments on one level will be ordered by date of creation
		order_insertion_by=['submit_time']

	def is_editable(self):
		interval = timedelta(seconds=15*60)
		now = timezone.now()
		now-=interval
		return self.submit_time>now

	def user_voted(self, user):
		return CommentVote.objects.filter(comment=self).filter(voter=user).exists()
	def get_score(self):
		score = CommentVote.objects.filter(comment=self).aggregate(Sum('score'))['score__sum']
		if score is None:
			score=0
		return score


	def get_score_formatted(self):
		score = self.get_score()
		if score >= 10000:
			formatted_number = float(score) / 1000
			formatted_number = str(formatted_number)[:4] + 'k'
			return formatted_number
		else:
			return score

	def time_since_submit(self):
		return timezone.now() - self.submit_time

	def __unicode__(self):
		return self.text



SCORES = (
	(+1, u'+1'),
	(-1, u'-1'),
)

class Vote(models.Model):
	voter = models.ForeignKey(User, on_delete=models.CASCADE)
	score = models.SmallIntegerField(choices=SCORES)
	class Meta:
		abstract = True


class PostVote(Vote):
	post = models.ForeignKey(Post, on_delete=models.CASCADE)
	class Meta:
		unique_together = (("voter", "post",),)
	def __unicode__(self):
		return self.voter.first_name + " " + self.voter.last_name + " " + str(self.score) + " " + self.post.title


class CommentVote(Vote):
	comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
	class Meta:
		unique_together = (("voter", "comment",),)
	def __unicode__(self):
		return self.voter.first_name + " " + self.voter.last_name + " " \
		       + str(self.score) + " on " + self.comment.post.title + " by " + self.comment.author.username


class PostFlag(models.Model):
	post = models.ForeignKey(Post, on_delete=models.CASCADE)
	flagger = models.ForeignKey(User, on_delete=models.CASCADE)
	def __unicode__(self):
		return self.flagger.first_name + " " + self.flagger.last_name + " flagged " + self.post.title


class UserNewsSuggestion(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	url = models.URLField(max_length=150)

	def __str__(self):
		return "{url} | {user}".format(url=urlparse(self.url).netloc, user=self.user.email)


class FeedlyAPISettings(SingletonModel):
	FEEDLY_API_CLIENT_ID = models.CharField(blank=True, help_text='Use “feedlydev” for the client_id'
	                                                  ' if you have developer access token', max_length=400,
	                                        default='feedlydev')
	FEEDLY_API_CLIENT_SECRET = models.CharField(blank=True, help_text='Use “feedlydev” for the client_secret'
	                                                  ' if you have developer access token', max_length=400,
	                                            default='feedlydev')
	FEEDLY_API_REFRESH_TOKEN = models.CharField(blank=True, max_length=400)
	FEEDLY_API_ACCESS_TOKEN = models.CharField(blank=True, max_length=400, help_text="Automatically refreshes"
	                                                                 " if you have feedly pro or team account")
	api_requests_remained = models.IntegerField(default=250)


	def get_client(self):
		return FeedlyClient(feedly_config=self, sandbox=False)


	def set_api_requests_remained(self, headers):
		"""Takes from headers of Feedly's response limit and counter of requests"""
		try:
			self.api_requests_remained = int(headers.get('X-RateLimit-Limit')) - int(headers.get('X-RateLimit-Count'))
		except ValueError:
			raise Exception('Feedly\'s response headers are changed or incorrect.')

		self.save()
		return self.api_requests_remained


	def __str__(self):
		return "Feedly Configuration"

	class Meta:
		verbose_name = "Feedly Configuration"

