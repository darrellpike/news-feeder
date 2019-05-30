from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from posts.models import *
from django.template.response import TemplateResponse, SimpleTemplateResponse
from posts.forms import PostVoteForm, CustomRegistrationForm, CustomPasswordResetForm, UserProfileUpdateForm,\
	ChangeUserImageForm, NewNewsSuggestionForm, NewCommentForm, CommentVoteForm
from django_registration.backends.activation.views import ActivationView
from django.urls import reverse, reverse_lazy
from posts.utils import DeltaFirstPagePaginator
from posts.tasks import create_or_update_contact_hubspot, update_contact_property_hubspot
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.db.models import Q
import operator
from functools import reduce
from django.db import IntegrityError
from django.template.loader import render_to_string
from django_registration.backends.activation.views import RegistrationView
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from posts.models import FeedlyAPISettings

class AjaxableResponseMixin(object):
	"""
	Mixin to add AJAX support to a form.
	Must be used with an object-based FormView (e.g. CreateView)
	"""
	def form_invalid(self, form):
		response = super().form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		# We make sure to call the parent's form_valid() method because
		# it might do some processing (in the case of CreateView, it will
		# call form.save() for example).
		response = super().form_valid(form)
		if self.request.is_ajax():
			if self.ajax_template_name:
				html = render_to_string(self.ajax_template_name, {'object': self.object})
				return HttpResponse(html)
			else:
				data = {
					'pk': self.object.pk,
				}
				return JsonResponse(data)
		else:
			return response


class IndexView(generic.ListView):
	template_name = 'posts/index.html'
	context_object_name = 'news'
	model = Post
	paginate_by = 20

	def get_queryset(self):
		posts = Post.objects.all().filter(submit_time__lt=timezone.now()).order_by('-submit_time').annotate(
			score=Sum('postvote__score'))
		posts = posts.exclude(Q(submitter__userprofile__is_shadowbanned=True) & ~Q(submitter=self.request.user.id))
		for p in posts:
			p.ranking = p.get_ranking(score=p.score)
		posts = sorted(posts, key=operator.attrgetter('ranking'), reverse=True)
		return posts

	def get_context_data(self, **kwargs):
		context = super(IndexView, self).get_context_data(**kwargs)
		latest_news = Post.objects.filter(submit_time__lt=timezone.now()).order_by('-submit_time')[:5]
		context['latest_news'] = latest_news
		context['active'] = 'active'
		from posts.tasks import get_feedly_articles
		articles = get_feedly_articles()
		return context


class IndexPopularView(generic.ListView):
	template_name = 'posts/index_popular.html'
	context_object_name = 'news'
	model = Post
	paginate_by = 20

	def get_queryset(self):
		posts = Post.objects.all().filter(submit_time__lt=timezone.now()).order_by('-submit_time').annotate(
			score=Sum('postvote__score'))
		posts = posts.exclude(Q(submitter__userprofile__is_shadowbanned=True) & ~Q(submitter=self.request.user.id))
		for p in posts:
			p.ranking = p.get_ranking(score=p.score)
		posts = sorted(posts, key=operator.attrgetter('ranking'), reverse=True)
		return posts

	def get_context_data(self, **kwargs):
		context = super(IndexPopularView, self).get_context_data(**kwargs)
		return context


class IndexLatestView(generic.ListView):
	template_name = 'posts/index_latest.html'
	context_object_name = 'news'
	model = Post
	paginate_by = 20

	def get_queryset(self):
		return Post.objects.filter(submit_time__lt=timezone.now()).order_by('-submit_time')

	def get_context_data(self, **kwargs):
		context = super(IndexLatestView, self).get_context_data(**kwargs)
		return context


class PostDetailView(generic.DetailView):
	ajax_template_name = 'partial/post_modal_view.html'
	template_name = 'posts/post_view.html'
	model = Post
	context_object_name = 'article'

	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			self.template_name = self.ajax_template_name
		return super().get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(PostDetailView, self).get_context_data(**kwargs)
		context['comments'] = context['article'].comment_set.filter(parent=None).order_by('-submit_time')
		return context


class SearchView(generic.ListView):
	template_name = 'posts/search_ajax.html'
	context_object_name = 'search_results'
	model = Post
	paginator_class = DeltaFirstPagePaginator
	paginate_by = 10
	paginate_orphans = 5

	deltafirst = paginate_by - 3

	def get_top_search_results(self):
		query = self.request.GET.get('q', '')
		query_list = query.split(' ')
		posts = Post.objects.all().filter(reduce(operator.or_, (Q(title__icontains=x) for x in query_list)) | \
		                                  reduce(operator.or_, (Q(article_text__icontains=x) for x in query_list)) | \
		                                  reduce(operator.or_, (Q(text__icontains=x) for x in query_list)))
		posts = posts.annotate(score=Sum('postvote__score')).order_by('-score')[:3]
		return posts

	def get_queryset(self):
		query = self.request.GET.get('q', '')
		query_list = query.split(' ')
		posts = Post.objects.all().filter(reduce(operator.or_, (Q(title__icontains=x) for x in query_list)) | \
		                                  reduce(operator.or_, (Q(article_text__icontains=x) for x in query_list)) | \
		                                  reduce(operator.or_, (Q(text__icontains=x) for x in query_list)))
		posts = posts.exclude(id__in=self.get_top_search_results()).annotate(score=Sum('postvote__score')).order_by('-submit_time')
		return posts


	def get_paginator(self, queryset, per_page, orphans=0,
                      allow_empty_first_page=True, **kwargs):
		kwargs.update({'deltafirst': self.deltafirst})
		return super(SearchView, self).get_paginator(queryset, per_page, orphans=0,
                      allow_empty_first_page=True, **kwargs)



	def get_context_data(self, **kwargs):
		context = super(SearchView, self).get_context_data(**kwargs)
		if context['page_obj'].number == 1:
			context['top_search_results'] = self.get_top_search_results()
			count_total_results = self.get_queryset().count() + context['top_search_results'].count()
			if count_total_results > 0:
				context['total_results'] = count_total_results
		return context


@login_required(login_url=reverse_lazy('login'))
def vote_post(request, post_id):
	if request.user.is_authenticated and request.POST:
		vote = PostVote(voter=request.user, score=1)
		# if request.user.userprofile.count_karma()<500:
		# 	return HttpResponse('Not enough carma')
		if post_id:
			post = get_object_or_404(Post, pk=post_id)
			data = {
				'post': post.pk,
				'csrfmiddlewaretoken': request.POST['csrfmiddlewaretoken']
			}
			form = PostVoteForm(data, instance=vote)
			if form.is_valid():
				up_vote = True
				try:
					vote = form.save()
				except IntegrityError:
					post.postvote_set.filter(voter=request.user).delete()
					up_vote = False
				return JsonResponse({'up_vote': up_vote, 'score': post.get_score_formatted()})
			else:
				print(form.errors)
	return HttpResponse(0)


class CustomRegistrationView(RegistrationView):
	form_class = CustomRegistrationForm
	success_url = '/'
	template_name = 'django_registration/with_base/registration_form.html'
	ajax_template_name = 'django_registration/registration_form.html'
	success_template = 'django_registration/registration_complete.html'

	def create_inactive_user(self, form):
		"""
		Create the inactive user account and send an email containing
		activation instructions.

		"""
		new_user = form.save(commit=False)
		new_user.is_active = False
		new_user.save()

		response = create_or_update_contact_hubspot.delay(new_user.id, self.get_activation_key(new_user))


		return new_user


	def get(self, request, *args, **kwargs):
		response = super().get(request, *args, **kwargs)
		if request.is_ajax():
			self.template_name = self.ajax_template_name
			return render(request, self.template_name, context=self.get_context_data())
		else:
			return response

	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)
		if request.is_ajax():
			if response.status_code == 302:
				return TemplateResponse(request, self.success_template)
			else:
				errors = response.context_data['form'].errors
				response = JsonResponse(errors)
				response.status_code = 422
				return response
		else:
			return response

class CustomLoginView(LoginView):
	template_name = 'django_registration/with_base/login.html'
	ajax_template_name = 'django_registration/registration_login.html'

	def get(self, request, *args, **kwargs):
		if request.is_ajax():
			self.template_name = self.ajax_template_name
			return render(request, self.template_name, context=self.get_context_data())
		else:
			return HttpResponseRedirect('/?login=true')

	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)
		if request.is_ajax():
			if response.status_code == 302:
				index = reverse('index')
				return JsonResponse({'url': index})
			else:
				errors = response.context_data['form'].errors
				response = JsonResponse(errors)
				response.status_code = 422
				return response
		else:
			return HttpResponseRedirect('/?login=true')


class CustomPasswordResetView(PasswordResetView):
	ajax_template_name = 'django_registration/password_reset.html'
	template_name = 'django_registration/with_base/password_reset.html'
	form_class = CustomPasswordResetForm

	def get(self, request, *args, **kwargs):
		response = super().get(request, *args, **kwargs)
		if request.is_ajax():
			self.template_name = self.ajax_template_name
			return render(request, self.template_name, context=self.get_context_data())
		else:
			return response

	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)
		if request.is_ajax():
			if response.status_code == 302:
				return JsonResponse({'url': response.url})
			else:
				errors = response.context_data['form'].errors
				response = JsonResponse(errors)
				response.status_code = 422
				return response
		else:
			return response


class CustomActivationView(ActivationView):
	def activate(self, *args, **kwargs):
		user = super().activate(*args, **kwargs)
		update_contact_property_hubspot.delay(user.email, 'email_confirmed', True)
		return user


class UserProfileView(LoginRequiredMixin, generic.UpdateView):
	model = UserProfile
	form_class = UserProfileUpdateForm
	template_name = 'posts/profile.html'
	success_url = reverse_lazy('profile')

	def get_object(self, queryset=None):
		return self.request.user

	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)
		if request.is_ajax():
			if response.status_code == 302:
				return JsonResponse({'url': response.url})
			else:
				errors = response.context_data['form'].errors
				response = JsonResponse(errors)
				response.status_code = 422
				return response
		else:
			return response

@login_required(login_url=reverse_lazy('login'))
def change_user_profile_image(request):
	if request.user.is_authenticated and request.method == 'POST':
		form = ChangeUserImageForm(request.POST, request.FILES)
		if form.is_valid():
			m = UserProfile.objects.get(user__pk=request.user.pk)
			m.image = form.cleaned_data['new_image']
			m.save()
			return JsonResponse({'new_image_url': m.image_thumbnail_md.url})
		else:
			response = JsonResponse(form.errors)
			response.status_code = 422
			return response
	else:
		return HttpResponseForbidden('allowed only via POST')


class NewNewsSuggestionView(LoginRequiredMixin, generic.edit.CreateView):
	template_name = 'partial/modal_suggest_news.html'
	ajax_template_name = 'partial/modal_suggest_news.html'
	success_url = reverse_lazy('index')
	success_template = 'partial/modal_suggest_news_success.html'
	model = UserNewsSuggestion
	form_class = NewNewsSuggestionForm

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)

	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)
		if request.is_ajax():
			if response.status_code == 302:
				return TemplateResponse(request, self.success_template)
			else:
				errors = response.context_data['form'].errors
				response = JsonResponse(errors)
				response.status_code = 422
				return response
		else:
			return response


@login_required(login_url=reverse_lazy('login'))
def new_comment(request, post_id, parent_id=None):
	if request.user.is_authenticated and request.method == 'POST':
		post = get_object_or_404(Post, pk=post_id)
		parent = None
		if not parent_id is None:
			parent = get_object_or_404(Comment, pk=parent_id)
			if parent.post != post:
				raise Http404

		new_comment = Comment(author=request.user, post=post, parent=parent)
		new_comment_form = NewCommentForm(request.POST, instance=new_comment)

		if new_comment_form.is_valid():
			new_comment = new_comment_form.save()
			return TemplateResponse(request, 'partial/comment.html', context={'comment': new_comment, 'new': True})
		else:
			response = JsonResponse(new_comment_form.errors)
			response.status_code = 422
			return response

@login_required(login_url=reverse_lazy('login'))
def vote_comment(request, post_id, comment_id):
	if request.user.is_authenticated and request.method == 'POST':
		post = get_object_or_404(Post, pk=post_id)
		comment = get_object_or_404(Comment, pk=comment_id)
		vote = CommentVote(comment=comment, voter=request.user, score=1)
		data = {
			'comment': comment.pk,
			'csrfmiddlewaretoken': request.POST['csrfmiddlewaretoken']
		}
		form = CommentVoteForm(data, instance=vote)
		if form.is_valid():
			up_vote = True
			try:
				vote = form.save()
			except IntegrityError:
				comment.commentvote_set.filter(voter=request.user).delete()
				up_vote = False
			return JsonResponse({'up_vote': up_vote, 'score': comment.get_score_formatted()})
		else:
			print(form.errors)
	return HttpResponse(0)


def comment_sort(request, post_id):
	if request.GET and post_id:
		template = 'partial/comments_body.html'
		sort = request.GET.get('sort', False)
		try:
			post = Post.objects.prefetch_related('comment_set').get(pk=post_id)
		except Post.DoesNotExist:
			raise Http404
		comments = post.comment_set.filter(parent=None)
		if sort:
			if sort == 'oldest':
				comments = comments.order_by('submit_time')
			elif sort == 'popular':
				comments = sorted(comments.all(), key=lambda c: -c.get_score())
			else:
				comments = comments.order_by('-submit_time')


		return TemplateResponse(request, template, context={'comments': comments})


def send_activation_again(request, email):
	if email:
		user = get_object_or_404(User, email=email)
		if not user.is_active:
			sent = False
			response = create_or_update_contact_hubspot.delay(user.id, user.get_activation_key())
			if response == 200:
				sent = True
			return SimpleTemplateResponse('django_registration/with_base/send_activation_again.html', context={
				'email': email,
				'sent': sent
			})
	raise Http404




