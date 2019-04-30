from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import MaxLengthValidator
from django_registration.signals import user_registered
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import DatabaseError
# from .utils import *
from django.db.models import Max
import random
import requests
from instagram.bind import InstagramClientError, InstagramAPIError
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit, Adjust
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail

CHAR_FIELD_MAX_LENGTH = 85

#BUFFER_TOKEN="1/2e1a5f4377c137037277b1018687db14"#testing
BUFFER_TOKEN="1/a87c16b5ef67c2978b55a34eaee28078"


class CustomUserManager(BaseUserManager):
	def create_user(self, email, first_name, last_name, password):
		user = self.model(email=email, first_name=first_name, last_name=last_name,  password=password)
		user.set_password(password)
		user.is_staff = False
		user.is_superuser = False
		user.save(using=self._db)
		return user

	def create_superuser(self, email, first_name, last_name, password):
		user = self.create_user(email=email, first_name=first_name, last_name=last_name, password=password)
		user.is_active = True
		user.is_staff = True
		user.is_superuser = True
		user.save(using=self._db)
		return user

	def get_by_natural_key(self, email_):
		print(email_)
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
	is_staff = models.BooleanField(default=False)
	date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
	is_active = models.BooleanField(default=False)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['first_name', 'last_name']

	objects = CustomUserManager()

	def get_full_name(self):
		"""
		Returns the first_name plus the last_name, with a space in between.
		"""
		full_name = '%s %s | %s' % (self.first_name, self.last_name, self.email)
		return full_name.strip()

	def get_short_name(self):
		return self.email

	def natural_key(self):
		return self.email

	def email_user(self, subject, message, from_email=None, **kwargs):
		"""
		Sends an email to this User.
		"""
		send_mail(subject, message, from_email, [self.email], **kwargs)

	def __str__(self):
		full_name = '%s %s | %s' % (self.first_name, self.last_name, self.email)
		return full_name.strip()

class UserProfile(models.Model):
	user = models.OneToOneField(User, primary_key=True, editable=False, on_delete=models.CASCADE)
	description = models.TextField(blank=True, validators=[MaxLengthValidator(500)])
	is_email_public = models.BooleanField(default=False)
	is_shadowbanned = models.BooleanField(default=False)
	is_fake = models.BooleanField(default=False)

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
	if created and User.objects.all().count()>1:
		#this >1 check is needed for the initial syncdb, since south prevents the userprofile
		#table from being built
		profile = UserProfile(user=instance)
		profile.save()

class Post(models.Model):
	title = models.CharField(max_length=85)
	submitter = models.ForeignKey(User, on_delete=models.CASCADE)
	submit_time = models.DateTimeField(default=timezone.now)
	url = models.URLField(max_length=300, blank=True)
	label_for_url = models.CharField(max_length=85, blank=True)
	text = models.TextField(blank=True)
	article_text = models.TextField(blank=True)
	news_site_logo = ProcessedImageField(upload_to='news_site_logos/',
	                                     processors=[ResizeToFit(100,100)],
	                                     format='JPEG',
	                                     null=True)
	image = models.ImageField(blank=True)

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
	def get_ranking(self,score=None):
		if score is None:
			score=self.get_score()
		timediff = timezone.now() - self.submit_time
		hours_since = timediff.seconds/60./60 + timediff.days*24.
		return calculate_rank(score,hours_since)
	# def buffer_time(self):
	# 	latest_post = Post.objects.all().aggregate(Max('submit_time'))
	# 	interval = timedelta(minutes=60+random.randint(1,30))
	# 	publish_time = max(latest_post['submit_time__max'], timezone.now()) + interval
	# 	self.submit_time=publish_time
	# 	print("saving new submit time")
	# 	self.save()
	# 	print("saved new submit time. calling create_buffers")
	# 	self.create_buffers()
	# 	print("called create_buffers")
	#
	# def create_buffers(self):
	# 	profile_ids = []
	# 	for bp in BufferProfile.objects.all():
	# 		profile_ids += [bp.profile_id]
	# 	if profile_ids == []: return
	# 	url = "https://api.bufferapp.com/1/updates/create.json"
	# 	payload={"text":"https://www.plantdietlife.com"+reverse('view_post', args=(self.pk,))+" "+self.title,
	# 	         "profile_ids[]":profile_ids,
	# 	         "scheduled_at":self.submit_time.isoformat(),
	# 	         "access_token":BUFFER_TOKEN,
	# 	         }
	# 	r = requests.post(url, data=payload)
	# 	response=r.json()
	# 	print response
	# 	response = response['updates']
	# 	for r in response:
	# 		new_id = r['id']
	# 		buffer_item = BufferItem(post=self, item_id=new_id)
	# 		buffer_item.save()
	# #url = 'https://api.bufferapp.com/1/updates/create.json'
	# #curl --data "access_token=1/2e1a5f4377c137037277b1018687db14&text=This%20is%20an%20example%20update&profile_ids[]=524d95d9718355b01100002e" https://api.bufferapp.com/1/updates/create.json
	# def update_buffers(self):
	# 	for item in self.bufferitem_set.all():
	# 		url = "https://api.bufferapp.com/1/updates/"+item.item_id+"/update.json"
	# 		payload={"text":"https://www.plantdietlife.com"+reverse('view_post', args=(self.pk,))+" "+self.title,
	# 		         "scheduled_at":self.submit_time.isoformat(),
	# 		         "access_token":BUFFER_TOKEN,
	# 		         }
	# 		r = requests.post(url, data=payload)
	# def destroy_buffers(self):
	# 	for item in self.bufferitem_set.all():
	# 		url = "https://api.bufferapp.com/1/updates/"+item.item_id+"/destroy.json"
	# 		payload={"access_token":BUFFER_TOKEN,}
	# 		r = requests.post(url, data=payload)

	def __unicode__(self):
		return self.title

def calculate_rank(score,hours_since):
	return (score-.9)# / (hours_since + 2)**1.8

# @receiver(post_save, sender=Post)
# def save_article(sender, instance, created, **kwarg):
# 	if instance.url and not instance.article_text:
# 		url = instance.url
# 		if url:
# 			embedly_info = get_embedly_info(url)
# 			if 'content' in embedly_info:
# 				if embedly_info['content']:
# 					instance.article_text = embedly_info['content']
# 					instance.save()
# 			if 'related' in embedly_info:
# 				if embedly_info['related']:
# 					for r in embedly_info.get('related',[]):
# 						try:
# 							related_article = RelatedArticle(post=instance, url=r.url, title=r.title[:85])
# 							related_article.save()
# 						except TypeError:
# 							continue
#
# 	elif instance.submit_time>timezone.now():
# 		if not created:
# 			instance.update_buffers()

# @receiver(pre_delete, sender=Post)
# def delete_from_buffer(sender, instance, **kwarg):
# 	instance.destroy_buffers()
#
# class BufferProfile(models.Model):
# 	profile_id = models.CharField(max_length=60, primary_key=True)
# 	profile_description = models.TextField(blank=True)
# 	def __unicode__(self):
# 		return self.profile_description
#
# class BufferItem(models.Model):
# 	post = models.ForeignKey(Post)
# 	item_id = models.CharField(blank=True, max_length=60, primary_key=True)
#
# class RelatedArticle(models.Model):
# 	post = models.ForeignKey(Post)
# 	url = models.URLField(max_length=300, blank=True)
# 	title = models.CharField(max_length=85)
# 	def __unicode__(self):
# 		return self.title

class Comment(MPTTModel):
	author = models.ForeignKey(User, on_delete=models.CASCADE)
	post = models.ForeignKey(Post, editable=False, on_delete=models.CASCADE)
	submit_time = models.DateTimeField(auto_now_add=True)
	text = models.TextField(blank=False)

	parent = TreeForeignKey('self', null=True, blank=True, related_name='children', editable=False, on_delete=models.PROTECT)

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
		return self.voter.first_name + " " + self.voter.last_name + " " + str(self.score) + " on " + self.comment.post.title + " by " + self.comment.author.username

@receiver(post_save, sender=Comment)
def auto_upvote_comment(sender, instance, created, **kwargs):
	if created:
		vote = CommentVote(comment=instance, voter=instance.author, score=1)
		vote.save()

class PostFlag(models.Model):
	post = models.ForeignKey(Post, on_delete=models.CASCADE)
	flagger = models.ForeignKey(User, on_delete=models.CASCADE)
	def __unicode__(self):
		return self.flagger.first_name + " " + self.flagger.last_name + " flagged " + self.post.title

# class InstagramImage(models.Model):
# 	tag = models.CharField(max_length=127)
# 	tags = models.TextField()
# 	num_tags = models.PositiveIntegerField()
# 	image_url_lowres = models.URLField()
# 	image_url_standardres = models.URLField()
# 	image_url_thumbnail = models.URLField()
# 	caption = models.TextField()
# 	submitter_username = models.CharField(max_length=127)
# 	submitter_full_name = models.CharField(max_length=127)
# 	submitter_picture_url = models.URLField()
# 	submitter_id = models.CharField(max_length=127)
# 	instagram_id = models.CharField(max_length=127, unique=True)
# 	num_likes = models.PositiveIntegerField()
# 	created_time = models.DateTimeField()
# 	link = models.URLField()
#
# 	def refetch_info(self):
# 		try:
# 			image_info, comments = parse_instagram_to_dic(get_instagram_image(self.instagram_id))
# 			InstagramImage.objects.filter(pk=self.pk).update(**image_info)
# 			print image_info, comments
# 			for c in comments:
# 				c['image']=self
# 				comment, comment_created = InstagramComment.objects.get_or_create(instagram_id=c['instagram_id'], defaults=c)
# 				if not comment_created:
# 					InstagramComment.objects.filter(pk=comment.pk).update(**c)
# 		except InstagramClientError:
# 			print "InstagramClientError!"
# 		except InstagramAPIError, e:
# 			print "not found!"
# 			if e.error_type=='APINotFoundError':
# 				self.delete()
#
#
# 	def __unicode__(self):
# 		return '"' + self.caption + '"' + "submitted by " + self.submitter_username
#
# class InstagramComment(models.Model):
# 	body = models.TextField()
# 	submitter_username = models.CharField(max_length=127)
# 	submitter_full_name = models.CharField(max_length=127)
# 	submitter_profile_picture = models.URLField()
# 	submitter_id = models.CharField(max_length=127)
# 	instagram_id = models.CharField(max_length=127, unique=True)
# 	image = models.ForeignKey(InstagramImage)
# 	created_time = models.DateTimeField()
#
# class InstagramHashtagsToFetch(models.Model):
# 	tag = models.CharField(max_length=127)
# #TODO: all images for a tag are accessed via https://api.instagram.com/v1/tags/vegan/media/recent?client_id=dc4fe565bfd940dcb4f12834634b4013
# #img id is accessed by json['images']['standard_resolution']['url'] or json['images']['low_resolution']['url']
# #comments are json['comments']['data'], which then gives a list. each comment then has comment['text'], comment['from']['username'], comment['from']['profile_picture']
# #example json:
# #created_time are in "time since epoch" (in seconds)
# """
# json ={
#          "attribution":null,
#          "tags":[
#             "vegetarian",
#             "foodie",
#             "vegan",
#             "southasian"
#          ],
#          "location":null,
#          "comments":{
#             "count":1,
#             "data":[
#                {
#                   "created_time":"1396822596",
#                   "text":"#vegan #foodie #southasian #vegetarian",
#                   "from":{
#                      "username":"elainechandow",
#                      "profile_picture":"http:\/\/images.ak.instagram.com\/profiles\/anonymousUser.jpg",
#                      "id":"319310606",
#                      "full_name":"elaine"
#                   },
#                   "id":"692920616911207521"
#                }
#             ]
#          },
#          "filter":"Amaro",
#          "created_time":"1396822531",
#          "link":"http:\/\/instagram.com\/p\/mdvyL6iX3j\/",
#          "likes":{
#             "count":0,
#             "data":[
#
#             ]
#          },
#          "images":{
#             "low_resolution":{
#                "url":"http:\/\/distilleryimage1.s3.amazonaws.com\/cfe0a786bdd811e3afc612cd81b9cc59_6.jpg",
#                "width":306,
#                "height":306
#             },
#             "thumbnail":{
#                "url":"http:\/\/distilleryimage1.s3.amazonaws.com\/cfe0a786bdd811e3afc612cd81b9cc59_5.jpg",
#                "width":150,
#                "height":150
#             },
#             "standard_resolution":{
#                "url":"http:\/\/distilleryimage1.s3.amazonaws.com\/cfe0a786bdd811e3afc612cd81b9cc59_8.jpg",
#                "width":640,
#                "height":640
#             }
#          },
#          "users_in_photo":[
#
#          ],
#          "caption":{
#             "created_time":"1396822531",
#             "text":"Lentil Soup, Vegetarian Somosa and chutney sauce",
#             "from":{
#                "username":"elainechandow",
#                "profile_picture":"http:\/\/images.ak.instagram.com\/profiles\/anonymousUser.jpg",
#                "id":"319310606",
#                "full_name":"elaine"
#             },
#             "id":"692920075082628167"
#          },
#          "type":"image",
#          "id":"692920074638032355_319310606",
#          "user":{
#             "username":"elainechandow",
#             "website":"",
#             "profile_picture":"http:\/\/images.ak.instagram.com\/profiles\/anonymousUser.jpg",
#             "full_name":"elaine",
#             "bio":"",
#             "id":"319310606"
#          }
#       }
# """
