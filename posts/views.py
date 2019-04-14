from django.http import HttpResponse, HttpResponseRedirect, Http404
from posts.models import *
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.db.models import Q
import operator
from django.core.paginator import InvalidPage


class IndexView(generic.ListView):
	template_name = 'new_index.html'
	context_object_name = 'news'
	model = Post
	paginate_by = 2

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
		return context
