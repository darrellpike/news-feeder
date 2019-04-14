from django.http import HttpResponse, HttpResponseRedirect, Http404
from posts.models import *
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.views import generic


class IndexView(generic.ListView):
	template_name = 'new_index.html'
	context_object_name = 'news'
	model = Post

	def get_context_data(self, **kwargs):
		context = super(IndexView, self).get_context_data(**kwargs)
		latest_news = Post.objects.filter(submit_time__lte=timezone.now())[:3]
		context['latest_news'] = latest_news
		return context
