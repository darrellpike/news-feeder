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


class AjaxableResponseMixin:
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

class SearchView(generic.ListView):
	template_name = 'search_ajax.html'
	context_object_name = 'search_results'
	model = Post
	paginate_by = 7

	def get_queryset(self):
		(posts, comments) = ([], [])
		query = self.request.GET.get('q', '')
		query_list = query.split(' ')
		sort_type = self.request.GET.get('sort', 'points')
		query_type = self.request.GET.get('type', 'posts')
		if sort_type == 'points':
			sort_by = '-score'
		else:
			sort_by = '-submit_time'
		posts = Post.objects.all().filter(reduce(operator.or_, (Q(title__icontains=x) for x in query_list)) | \
		                                  reduce(operator.or_, (Q(article_text__icontains=x) for x in query_list)) | \
		                                  reduce(operator.or_, (Q(text__icontains=x) for x in query_list)))
		posts = posts.annotate(score=Sum('postvote__score')).order_by(sort_by)
		posts = paginate_items(self.request.GET.get('page'), posts, 25)
		return posts


	def get_context_data(self, **kwargs):
		context = super(SearchView, self).get_context_data(**kwargs)
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