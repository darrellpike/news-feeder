from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, Http404
from posts.models import *
from posts.forms import PostVoteForm
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.db.models import Q
import operator
from django.db import IntegrityError
from django.core.paginator import InvalidPage
from django.template.loader import render_to_string


class AjaxableResponseMixin(object):
	"""
	Mixin to add AJAX support to a form.
	Must be used with an object-based FormView (e.g. CreateView)
	"""
	def form_invalid(self, form):
		response = super(AjaxableResponseMixin, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		# We make sure to call the parent's form_valid() method because
		# it might do some processing (in the case of CreateView, it will
		# call form.save() for example).
		response = super(AjaxableResponseMixin, self).form_valid(form)
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
	template_name = 'new_index.html'
	context_object_name = 'news'
	model = Post
	paginate_by = 7

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
		latest_news = Post.objects.filter(submit_time__lt=timezone.now()).order_by('-submit_time')[:3]
		context['latest_news'] = latest_news
		context['active'] = 'active'
		return context


class IndexLatestView(generic.ListView):
	template_name = 'latest_index.html'
	context_object_name = 'news'
	model = Post
	paginate_by = 7

	def get_queryset(self):
		return Post.objects.filter(submit_time__lt=timezone.now()).order_by('-submit_time')

	def get_context_data(self, **kwargs):
		context = super(IndexLatestView, self).get_context_data(**kwargs)
		context['active'] = 'active'
		return context


class PostDetailView(generic.DetailView):
	ajax_template_name = 'story_modal_view.html'
	template_name = 'story_modal_view.html'
	model = Post
	context_object_name = 'article'

	def get_context_data(self, **kwargs):
		context = super(PostDetailView, self).get_context_data(**kwargs)
		context['comments'] = context['article'].comment_set
		return context


def vote_post(request):
	if request.user.is_authenticated() and request.method == 'POST':
		vote = PostVote(voter=request.user)
		if int(request.POST.get('score',0)) < 1 and request.user.userprofile.count_karma()<500:
			return HttpResponse(0)
		form = PostVoteForm(request.POST, instance=vote)
		if form.is_valid():
			try:
				vote = form.save()
			except IntegrityError:
				return HttpResponse(0)
			return HttpResponse(1)
		else:
			print form.errors
	return HttpResponse(0)
