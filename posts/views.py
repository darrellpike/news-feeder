from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from posts.models import *
from posts.forms import *
from util import *
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
import operator
from embedly import Embedly
from django.utils import timezone
import random
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from operator import attrgetter

def index(request, posts=None, images=None, header='new'):
    """
    show_vote_popover = request.session.get('show_vote_popover', True)
    if request.user.is_authenticated():
        show_vote_popover = False
    request.session['show_vote_popover']=False
    """
    if not posts:
        #django has a bug with multiple annotations, so I can't just annotate in the comment counts...https://code.djangoproject.com/ticket/10060
        posts = Post.objects.all().filter(submit_time__lt=timezone.now()).order_by('-submit_time').annotate(score=Sum('postvote__score'))

    posts=posts.exclude(Q(submitter__userprofile__is_shadowbanned=True) & ~Q(submitter=request.user.id))
    if header=='popular' or header=='ask':
        for p in posts:
            p.ranking=p.get_ranking(score=p.score)
        posts = sorted(posts, key=operator.attrgetter('ranking'), reverse=True)

        #posts=paginate_items(request.GET.get('page'),posts,25)
        
    if request.is_ajax():
        querystring_key=request.GET.get('querystring_key','')
        if querystring_key == 'images_page':
            template = "partial/image_template.html"
        else:
            template = "partial/post_template.html"
    else:
        template = "index.html"

    if images is None:
        images=InstagramImage.objects.all()
    #TODO: set this for a timer
    #for i in images:
    #    i.refetch_info()
    COLUMNS = 4
    posts_sublists = [posts[i:i+COLUMNS] for i in range(0, len(posts), COLUMNS)]
    images_sublists = [images[i:i+COLUMNS] for i in range(0, len(images), COLUMNS)]
    posts_and_images = zip(posts_sublists, images_sublists)
    return render(request, template,
                  { "posts": posts,
                    "images": images,
                    "posts_and_images": posts_and_images,
                    "header": header,
                    "new_post_form":PartialPostForm(),
#                   "show_vote_popover":show_vote_popover,
                    "hide_footer":True,
                    "show_menu":True
                  })

    #popular, latest, most comments, and #vegan (in this order). If the user chooses "#vegan" they should only see the most popular images with the vegan hashtag in them that has three or less total hashtags.
#TODO: don't bother fetching posts if ?images_page is defined, or images if ?page is defined
def index_ask(request):
    posts = Post.objects.all().filter(url='').filter(submit_time__lt=timezone.now()).annotate(score=Sum('postvote__score')).order_by('-submit_time').order_by()
    return index(request, posts=posts, header='ask')

def index_new(request):
    posts = Post.objects.all().filter(submit_time__lt=timezone.now()).annotate(score=Sum('postvote__score')).order_by('-submit_time')
    images = InstagramImage.objects.all().order_by("-created_time");
    return index(request, posts=posts, images=images, header='new')

def index_popular(request):
    images = InstagramImage.objects.all().order_by("-num_likes");
    return index(request, images=images, header='popular')

def index_most_comments(request):
    images = InstagramImage.objects.all().annotate(num_comments=Count('instagramcomment')).order_by("-num_comments");
    return index(request, images=images, header='most_comments')

def index_vegan(request):
    images = InstagramImage.objects.all().filter(tags__regex=r'vegan')
    return index(request, images=images, header='vegan')


@staff_member_required
def admin_scheduled_posts(request):
    posts = Post.objects.all().filter(submit_time__gt=timezone.now()).order_by('submit_time')
    return render(request, "dashboard_scheduled_posts.html",
                              {'header':'admin_dashboard',
                               'admin_header':'scheduled_posts',
                               'posts':posts,
                               })

@staff_member_required
def admin_active_users(request):
    users = UserProfile.objects.all().filter(is_fake=False)
    if request.method == 'GET':
        order_by=request.GET.get('order','')
        try:
            users = sorted(users.all(),key=operator.methodcaller(order_by), reverse=True)
            print order_by
        except AttributeError:
            users = sorted(users.all(),key=operator.methodcaller('post_count'), reverse=True)
    users = users[:25]
    return render(request, "dashboard_active_users.html",
                              {'header':'admin_dashboard',
                               'admin_header':'active_users',
                               'users':users,
                               })

@staff_member_required
def admin_stats_and_analytics(request):
    users = User.objects.all().filter(userprofile__is_fake=False)
    real_user_count = users.count()
    interval = timedelta(days=7)
    
    last_week_users = users.filter(date_joined__gt=timezone.now()-interval).count()
    last_last_week_users = users.filter(date_joined__gt=timezone.now()-interval-interval).filter(date_joined__lt=timezone.now()-interval).count()
    try:
        weekly_join_ratio = "{0:.2f}".format(float(last_week_users)/last_last_week_users)
    except ZeroDivisionError:
        weekly_join_ratio = "(can't divide by zero)"
        
    user_posts = Post.objects.all().filter(submitter__userprofile__is_fake=False)
    last_week_posts = user_posts.filter(submit_time__gt=timezone.now()-interval).count()
    last_last_week_posts = user_posts.filter(submit_time__gt=timezone.now()-interval-interval).filter(submit_time__lt=timezone.now()-interval).count()
    try:
        weekly_post_ratio = "{0:.2f}".format(float(last_week_posts)/last_last_week_posts)
    except ZeroDivisionError:
        weekly_post_ratio = "(can't divide by zero)"
        
    return render(request, "dashboard_stats_and_analytics.html",
                              {'header':'admin_dashboard',
                               'admin_header':'stats',
                               'real_user_count':real_user_count,
                               'last_week_user_count':last_week_users,
                               'last_last_week_user_count':last_last_week_users,
                               'weekly_join_ratio':weekly_join_ratio,
                               'last_week_post_count':last_week_posts,
                               'last_last_week_post_count':last_last_week_posts,
                               'weekly_post_ratio':weekly_post_ratio,                                   
                               })

@staff_member_required
def admin_buffer_profiles(request):
    if not request.user.is_staff:
        raise PermissionDenied
    if request.method == 'POST':
        if request.POST.get('action','')=="add":
            buffer_profile_form = BufferProfileForm(request.POST)
            if buffer_profile_form.is_valid():
                buffer_profile_form.save()
        if request.POST.get('action','')=="delete":
            buffer_profile = get_object_or_404(BufferProfile, pk=request.POST.get('profile_id'))
            buffer_profile.delete()

    url = "https://api.bufferapp.com/1/profiles.json?access_token="+BUFFER_TOKEN
    response = requests.get(url).json()
    for r in response:
        if BufferProfile.objects.filter(profile_id=r['_id']).exists():
            r['exists']=True
        r['id']=r['_id']
    return render(request, "dashboard_buffer_profiles.html",
                              {'header':'admin_dashboard',
                               'admin_header':'buffer_profiles',
                               'buffer_profiles':response,
                               })

def search(request):
    """
    Search has a sort_type (sort by date or sort by points) and a query_type (search posts or comments),
    in addition to a query of course (what terms to search for).

    This approach probably won't work for huge amounts of posts (plus it's not the best at sorting by relevance
    with many terms), but it's adequate to start with.
    """
    (posts, comments) = ([], [])
    query=request.GET.get('q','')
    query_list=query.split(' ')
    sort_type=request.GET.get('sort','points')
    query_type=request.GET.get('type','posts')
    if sort_type=='points':
        sort_by='-score'
    else:
        sort_by='-submit_time'
    if(query_type=='posts'):
        posts = Post.objects.all().filter(reduce(operator.or_, (Q(title__icontains=x) for x in query_list)) | \
                                              reduce(operator.or_, (Q(article_text__icontains=x) for x in query_list)) | \
                                              reduce(operator.or_, (Q(text__icontains=x) for x in query_list)))
        posts = posts.annotate(score=Sum('postvote__score')).order_by(sort_by)
        count = len(posts)
        posts=paginate_items(request.GET.get('page'),posts,25)
    else:
        comments = Comment.objects.all().filter(text__icontains=query)
        comments = comments.annotate(score=Sum('commentvote__score')).order_by(sort_by)
        count = len(comments)
        comments=paginate_items(request.GET.get('page'),comments,25)

    return render(request, "search.html",
                              { "posts": posts,
                                "comments": comments,
                                "count":count,
                                "query":query,
                                "sort_type":sort_type,
                                "query_type":query_type,
                                })

def view_post(request, post_id, new_comment_form=PartialCommentForm()):
    if post_id=="2" and not request.user.is_authenticated():
        #Login is required to view the feature requests...it's bad to do it
        #this way, but it's the quickest way
        return HttpResponseRedirect('/login/')
    post = get_object_or_404(Post, pk=post_id)
    if post.submit_time>timezone.now() and not request.user.is_staff: raise Http404
    post.score=post.get_score()
    if "<p>" in post.article_text and "</p>" in post.article_text:
        post.article_text=post.article_text.replace("<p>","<p><b>",1).replace("</p>","</b></p>",1)
    comments = Comment.objects.filter(post=post).order_by("-submit_time")
    return render(request, "view_post.html",
                              { "post": post,
                                "comments": comments,
                                'new_comment_form': new_comment_form,
                                'show_timestamp': True,
                                "article_length":len(post.article_text),
                                "preview_wordcount":max(int(.5*len(post.article_text.split(" "))),80)
                                })

def share_now(request, post_id):
    if not request.user.is_staff:
        raise PermissionDenied
    post = get_object_or_404(Post, pk=post_id)
    post.submit_time=timezone.now()
    post.save()
    return HttpResponseRedirect(reverse('view_post', args=(post.pk,)))

def view_comment(request, post_id, comment_id, new_comment_form=PartialCommentForm()):
    post = get_object_or_404(Post, pk=post_id)
    post.score=post.get_score()
    comment = get_object_or_404(Comment, pk=comment_id)
    comments = comment.get_descendants(include_self=False)
    return render(request, "view_comment.html",
                              { "post": post,
                                "comment": comment,
                                "comments": comments,
                                'new_comment_form': new_comment_form,
                                })

@login_required
def edit_comment(request, post_id, comment_id):
    if not request.user==post.submitter:
        raise PermissionDenied

    comment = get_object_or_404(Comment, pk=comment_id)
    post = get_object_or_404(Post, pk=post_id)
    if 'delete' in request.POST:
        if comment.is_editable() and comment.is_leaf_node():
            comment.delete()
            return HttpResponseRedirect(reverse('view_post', args=(post.pk,)))
    comments = comment.get_descendants(include_self=False)
    comment_form = PartialCommentForm(instance=comment)

    if request.method == 'POST':
        comment_form = PartialCommentForm(request.POST,instance=comment)
        if comment_form.is_valid():
            comment_form.save()
            return HttpResponseRedirect(reverse('view_post', args=(post.pk,)))
    else:
        comment_form = PartialCommentForm(instance=comment)
    return render(request, "edit_comment.html",
                              { "post": post,
                                "comment": comment,
                                "comments": comments,
                                "comment_form": comment_form,
                                })

def view_profile(request, user_id):
    if request.method == 'POST':
        return edit_profile(request,user_id)
    profile_owner = get_object_or_404(User, pk=user_id)
    form = None
    if request.user == profile_owner:
        form = PartialUserProfileForm(initial={'email':profile_owner.email,},instance=profile_owner.userprofile)
    return render(request, "view_profile.html",
                              { "profile_owner": profile_owner,
                                "form": form,
                                "owns_page": request.user==profile_owner
                                })

@login_required
def edit_profile(request,user_id):
    profile_owner = get_object_or_404(User, pk=user_id)
    if request.user!=profile_owner:
        raise PermissionDenied
    if request.method == 'POST':
        form = PartialUserProfileForm(request.POST,instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile changes saved!")
    else:
        form = PartialUserProfileForm(initial={'email':request.user.email,},instance=request.user.userprofile)
    return render(request, "view_profile.html",
                              {'profile_owner': profile_owner,
                               'form': form,
                               'owns_page': request.user==profile_owner})
    


def view_user_submissions(request,user_id):
    user = get_object_or_404(User, pk=user_id)
    posts = Post.objects.filter(submitter=user).order_by('-submit_time').annotate(score=Sum('postvote__score'))
    posts=paginate_items(request.GET.get('page'),posts,25)
    return render(request, "view_user_submissions.html",
                              { "show_user": user,
                                "posts": posts,
                                })

def view_user_comments(request,user_id):
    user = get_object_or_404(User, pk=user_id)
    comments = Comment.objects.filter(author=user).order_by('-submit_time')
    comments=paginate_items(request.GET.get('page'),comments,25)
    return render(request, "view_user_comments.html",
                              { "show_user": user,
                                "comments": comments,
                                })


@login_required
def add_comment(request, post_id, parent_id=None):
    if request.user.is_authenticated() and request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        parent=None
        if not parent_id is None:
            parent = get_object_or_404(Comment, pk=parent_id)
            if parent.post!=post:
                return HttpResponseRedirect(reverse("index"))
        
        new_comment = Comment(author=request.user,post=post,parent=parent)
        new_comment_form = PartialCommentForm(request.POST, instance=new_comment)
        
        if new_comment_form.is_valid():
            new_comment = new_comment_form.save()
            next_url = request.POST.get('next',reverse('view_post', args=(post.pk,)))
            return HttpResponseRedirect(next_url)
    else:
        new_comment_form = PartialCommentForm()
    if parent_id is None:
        return view_post(request, post_id, new_comment_form)
    else:
        return view_comment(request, post_id, parent_id, new_comment_form)

    
@login_required
def submit_post(request):
    if request.user.is_authenticated() and request.method == 'POST':
        user=request.user
        submitter=user
        
        new_username = request.POST.get('new_username')
        if request.user.is_staff and new_username:
            if not User.objects.filter(username=new_username).exists():
                submitter = User(username=new_username,password="567apple")
                submitter.save()
                submitter.userprofile.is_fake=True
                submitter.userprofile.save()

        new_post = Post(submitter=submitter)

        if request.user.is_staff and request.POST.get('buffer'):
            if not new_username:
                users=User.objects.all().filter(userprofile__is_fake=True)
                if users.exists():
                    new_post.submitter=random.choice(users)

        new_post_form = PartialPostForm(request.POST, instance=new_post)
        if new_post_form.is_valid():
            new_post = new_post_form.save()
            if request.POST.get('buffer'):
                new_post.buffer_time()
            next_url = request.POST.get('next',reverse('view_post', args=(new_post.pk,)))
            return HttpResponseRedirect(next_url)
    else:
        new_post_form = PartialPostForm()
    return render(request, "submit_post.html",
                              {'new_post_form': new_post_form,
                               })

@csrf_exempt
def admin_submit_post(request):
    if request.POST.get('secret')=='WZoWFOCGuNzA6pgnBY71JH8WpsZVDcPA':
        new_post = Post()
        users=User.objects.all().filter(userprofile__is_fake=True)
        if users.exists():
            new_post.submitter=random.choice(users)
        else:
            response = HttpResponse("You need to make a fake user first!")
            response['Access-Control-Allow-Origin']='*'
            return response
        new_post_form = PartialPostForm(request.POST, instance=new_post)
        if new_post_form.is_valid():
            print "about to save new post form"
            new_post = new_post_form.save()
            if not request.POST.get('share_now'):
                print "about to call buffer_time"
                new_post.buffer_time()
                print "finished calling buffer_time"
            post_url = reverse('view_post', args=(new_post.pk,))
            response = HttpResponse('Success! <a href="https://www.plantdietlife.com'+post_url+'" target="_blank">You can view the post here</a>')
            response['Access-Control-Allow-Origin']='*'
            return response
        else:
            #response = HttpResponse('Something went wrong!')
            response = HttpResponse("Error:"+str(new_post_form.errors))
            response['Access-Control-Allow-Origin']='*'
            return response
    else:
        response = HttpResponse('Your secret key is wrong.')
        response['Access-Control-Allow-Origin']='*'
        return response

@login_required
def buffer_post(request):
    if not request.user.is_staff: raise PermissionDenied

def vote_post(request):
    if request.user.is_authenticated() and request.method == 'POST':
        vote = PostVote(voter=request.user)
        if int(request.POST.get('score',0))<1 and request.user.userprofile.count_karma()<500:
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

def vote_comment(request):
    if request.user.is_authenticated() and request.method == 'POST':
        vote = CommentVote(voter=request.user)
        if int(request.POST.get('score',0))<1 and request.user.userprofile.count_karma()<500:
            return HttpResponse(0)
        form = CommentVoteForm(request.POST, instance=vote)
        if form.is_valid():
            try:
                vote = form.save()
            except IntegrityError:
                return HttpResponse(0)
            return HttpResponse(1)
        else:
            print form.errors
    return HttpResponse(0)


def email_share(request):
    post_id = request.POST.get('post_id','')
    if not post_id:
        messages.error(request, 'Oops! Something went wrong. Your email was not sent.')
        return HttpResponseRedirect(reverse("index"))
    post = get_object_or_404(Post, pk=post_id)

    send_to = request.POST.get('send_to', '')
    sender_name = request.POST.get('sender_name', '')
    send_from = request.POST.get('send_from', 'noreply@plantdietlife.com')
    message = request.POST.get('message', '')

    if not validate_email(send_to):
        messages.error(request, 'Oops! The email address you gave appears to be invalid.')
        return HttpResponseRedirect(reverse("index"))
    subject = sender_name + " shared a PLANTDIETlife post with you!"
    
    if not sender_name:
        sender_name="Someone"
    email_body = sender_name + " shared a PLANTDIETlife post with you!\n\n"
    if message:
        email_body += 'They said "'+message+'".\n\n'
    email_body += 'The post is called "'+post.title+'"\n\n'
    email_body += "Check it out here: https://www.plantdietlife.com"+reverse('view_post', args=(post.pk,))
    if send_to:
        try:
            send_mail(subject, email_body, send_from, [send_to])
        except BadHeaderError:
            messages.error(request, 'Oops! Something went wrong. Your email was not sent.')
            return HttpResponseRedirect(reverse("index"))
        messages.success(request, 'The post has been shared with ' + send_to)
        return HttpResponseRedirect(reverse("index"))
    else:
        messages.error(request, 'Oops! Something went wrong. Your email was not sent.')
        return HttpResponseRedirect(reverse("index"))
    return HttpResponseRedirect(reverse("index"))

@staff_member_required
def admin_delete_image(request, image_id):
    #TODO: this is vulnerable to CSRF. Not a huge deal because all images get deleted automatically anyway, but should be fixed
    image = get_object_or_404(InstagramImage, pk=image_id)
    image.delete()
    return HttpResponse(1)

@csrf_protect
def flag_post(request, post_id):
    if request.user.is_authenticated():
        flag = PostFlag(flagger=request.user,post = get_object_or_404(Post, pk=post_id))
        flag.save()
        messages.success(request, 'You have flagged this post for review by our moderators.')
        return HttpResponseRedirect(reverse('view_post', args=(post_id,)))
    return HttpResponseRedirect(reverse("index"))

"""
from configstore.configs import get_config

def about(request):
    config = get_config('About Page')
    return render_to_response("about.html",
                              {'static_text':config.get('text','Nothing here yet!'),
                               },
                              context_instance=RequestContext(request))   

def guidelines(request):
    config = get_config('Guidelines Page')
    return render_to_response("guidelines.html",
                              {'static_text':config.get('text','Nothing here yet!'),
                               },
                              context_instance=RequestContext(request))
"""
#These used to use the configstore module
def about(request):
    return render(request, "about.html")

def guidelines(request):
    return render(request, "guidelines.html")


#PLAN: on every hour, fetch the top 33 of each tag. Of those, keep the top 3 of each (in terms of number of comments/likes)
#On every half hour, re-fetch the comments for the top 50 or so images
#Every day, delete images older than 24 hours (to save space)?
#Remember, only 5k requests/day are allowed
def fetch_instagram_images(request):
    """
    tag = 'vegan'
    results = get_instagram_images(tag, 5)
    results=sorted(results,key=attrgetter('comments', 'likes'), reverse=True)
    for r in results[:35]:
        image_info, comments = parse_instagram_to_dic(r)
        image_info['tag']=tag
        image, created = InstagramImage.objects.get_or_create(instagram_id=r.id, defaults=image_info)
        if not created:
            InstagramImage.objects.filter(pk=image.pk).update(**image_info)
        for c in comments:
            c['image']=image
            comment, comment_created = InstagramComment.objects.get_or_create(instagram_id=c['instagram_id'], defaults=c)
            if not comment_created:
                InstagramComment.objects.filter(pk=comment.pk).update(**c)
    """
    return HttpResponse(1)
