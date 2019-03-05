from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django import forms
from django.core.urlresolvers import reverse
from embedly import Embedly
import socket
import requests
import mailchimp
from mailchimp import ListAlreadySubscribedError
from instagram.client import InstagramAPI
from instagram.bind import InstagramClientError, InstagramAPIError
import pytz

EMBEDLY_KEY = '715ad55204f44f7ba7c527343edafef6'

MAILCHIMP_API_KEY="d3ecb1d69ed36bfb37e675d612c45c21-us7"
MAILCHIMP_LIST_ID="7973a7ec84"

INSTAGRAM_CLIENT_ID="0ab9e87582164d049b5d8ec3cd1285a3"
INSTAGRAM_SECRET_CLIENT_ID="9172c4afe0ba4442b0803b0b862d28de"
INSTAGRAM_ACCESS_TOKEN='3292531766.0ab9e87.c3d1d66e706d45c790c92a5823c606ae'#(u'3292531766.0ab9e87.c3d1d66e706d45c790c92a5823c606ae', {u'username': u'motoranger.io', u'bio': u'', u'website': u'http://motoranger.io', u'profile_picture': u'https://scontent.cdninstagram.com/t51.2885-19/s150x150/13260921_544969179019715_275209978_a.jpg', u'full_name': u'suasponte', u'id': u'3292531766'})

def paginate_items(page, items, per_page):
    paginator = Paginator(items, per_page)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)
    return items

def validate_email(email):
    f = forms.EmailField()
    try:
        f.clean(email)
        return True
    except ValidationError:
        return False

def get_embedly_info(url):
    embedly = Embedly(EMBEDLY_KEY, timeout=6)#6 second timeout
    try:
        response = embedly.extract(url, words=2000)
        response_data = response.data
        #print json.dumps(response.__dict__)
        embedly_info = {}
        embedly_info['url']=url
        embedly_info['content']=response_data['content']
        related_list = response_data['related']
        embedly_info['related']=related_list
        return embedly_info
    except socket.error:
        #timeout
        return {}

def add_to_mailchimp(email):
    m=mailchimp.Mailchimp(MAILCHIMP_API_KEY)
    try:
        m.lists.subscribe(MAILCHIMP_LIST_ID, {'email':email }, double_optin=False)
    except ListAlreadySubscribedError:
        return
    except:#Fake or invalid email, just ignore it -- still let them sign up
        return
    return

def get_instagram_images(tag, num_results):
    try:
        print "making api..."
        api = InstagramAPI(access_token=INSTAGRAM_ACCESS_TOKEN, client_secret=INSTAGRAM_SECRET_CLIENT_ID)#client_id=INSTAGRAM_CLIENT_ID, client_secret=INSTAGRAM_SECRET_CLIENT_ID)
        print "made api. requesting...", num_results, tag
        tag_search, next_tag = api.tag_search(q=tag)
        print "tag search", tag_search, tag_search[0].name
        results, next_page = api.tag_recent_media(count=num_results, tag_name=tag_search[0].name)
        print "results:", results
        return results
    except InstagramClientError:
        print "InstagramClientError!"
        return []

def get_instagram_image(media_id):
    api = InstagramAPI(access_token=INSTAGRAM_ACCESS_TOKEN)#client_id=INSTAGRAM_CLIENT_ID)
    result = api.media(media_id)
    return result
    

def parse_instagram_to_dic(image):
    """
    Puts the image in a form suitable for passing to InstagramImage and
    InstagramComment object creation. You'll still need to set 'tag' on
    image_info and 'image' (the foreign key) on comments.
    """
    image_info = {}
    image_info['image_url_lowres']=image.images['low_resolution'].url
    image_info['image_url_standardres']=image.images['standard_resolution'].url
    image_info['image_url_thumbnail']=image.images['thumbnail'].url
    if image.caption:
        image_info['caption']=image.caption.text
    else:
        image_info['caption']=''
    image_info['submitter_username']=image.user.username
    image_info['submitter_full_name']=image.user.full_name
    image_info['submitter_picture_url']=image.user.profile_picture
    image_info['submitter_id']=image.user.id
    image_info['instagram_id']=image.id
    image_info['num_likes']=len(image.likes)
    image_info['created_time']=pytz.utc.localize(image.created_time)
    image_info['link']=image.link
    tags=[]
    if hasattr(image, 'tags'):
        for tag in image.tags:
            tags+=[tag.name]
        image_info['tags']=" ".join(tags)
    else:
        image_info['tags']="vegan"
    image_info['num_tags']=len(tags)
    comments = []
    for c in image.comments:
        comment_info = {}
        comment_info['body']=c.text
        comment_info['submitter_username']=c.user.username
        comment_info['submitter_full_name']=c.user.full_name
        comment_info['submitter_profile_picture']=c.user.profile_picture
        comment_info['submitter_id']=c.user.id
        comment_info['instagram_id']=c.id
        comment_info['created_time']=pytz.utc.localize(c.created_at)
        comments.append(comment_info)
    return image_info, comments
