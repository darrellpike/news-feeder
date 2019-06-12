from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.contrib import messages
from posts.tasks import create_or_update_contact_hubspot
from posts.models import UserProfile
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import requests

UserModel = get_user_model()


class CustomModelBackend(ModelBackend):

	"""
	Backend for returning 'Account is inactive' if it is.
	"""

	def authenticate(self, request, username=None, password=None, **kwargs):
		if username is None:
			username = kwargs.get(UserModel.USERNAME_FIELD)
		try:
			user = UserModel._default_manager.get_by_natural_key(username)
		except UserModel.DoesNotExist:
			# Run the default password hasher once to reduce the timing
			# difference between an existing and a nonexistent user (#20760).
			UserModel().set_password(password)
		else:
			if user.check_password(password):
				return user


def create_user(strategy, details, backend, user=None, *args, **kwargs):
	if user:
		return {'is_new': False}

	fields = dict((name, kwargs.get(name, details.get(name))) for name in [
		'first_name', 'last_name', 'password', 'email', 'username'])
	if not fields:
		return

	try:
		return {
			'is_new': True,
			'user': strategy.create_user(**fields)
		}
	except IntegrityError:
		messages.error(kwargs.get('request'), 'You have already registered via email, please log in.')


def activate_user(backend, user, response, *args, **kwargs):
	if backend.name == 'linkedin-oauth2' and user:
		user.is_active = True
		user.save()
		if not user.userprofile.hubspot_contact:
			create_or_update_contact_hubspot.delay(user_id=user.id)


def save_profile(backend, user, response, *args, **kwargs):
	if backend.name == 'linkedin-oauth2' and response.get('profilePicture', False):
		profile = user.userprofile
		if profile is None:
			profile = UserProfile(user_id=user.id)
		if profile.is_image_default():
			image_elements = response.get('profilePicture').get('displayImage~').get('elements')
			image_file = image_elements[len(image_elements) - 1].get('identifiers')[0]
			image_url = image_file.get('identifier')
			if image_url:
				img_temp = NamedTemporaryFile(delete=True)
				img_temp.write(requests.get(image_url).content)
				img_temp.flush()

				profile.image.save("{email}_{filename}".format(
					email=user.email, filename=image_file.get('filename', 'LinkedIn_image.jpeg')), File(img_temp))
				profile.save()
