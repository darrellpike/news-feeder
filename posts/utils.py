from django.core.paginator import EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
from django import forms
from django.core.paginator import Paginator, Page
import requests
import json
from posts.tasks import update_access_token_feedly
from urllib.parse import quote_plus


class DeltaFirstPagePaginator(Paginator):

    def __init__(self, object_list, per_page, orphans=0,
                 allow_empty_first_page=True, **kwargs):
        self.deltafirst = kwargs.pop('deltafirst', 0)
        Paginator.__init__(self, object_list, per_page, orphans,
                           allow_empty_first_page)

    def page(self, number):
        """Returns a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        if number == 1:
            bottom = 0
            if self.count > self.deltafirst:
                top = self.per_page - self.deltafirst
            else:
                top = self.per_page
        else:
            bottom = (number - 1) * self.per_page - self.deltafirst
            top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return Page(self.object_list[bottom:top], number, self)


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


class FeedlyClient(object):
    def __init__(self, **options):
        self.feedlyConfig = options.get('feedly_config')
        self.client_id = options.get('client_id', self.feedlyConfig.FEEDLY_API_CLIENT_ID)
        self.client_secret = options.get('client_secret', self.feedlyConfig.FEEDLY_API_CLIENT_SECRET)
        self.sandbox = options.get('sandbox', True)
        if self.sandbox:
            default_service_host = 'sandbox.feedly.com'
        else:
            default_service_host = 'cloud.feedly.com'
        self.service_host = options.get('service_host', default_service_host)
        self.additional_headers = options.get('additional_headers', {})
        self.token = options.get('token', self.feedlyConfig.FEEDLY_API_ACCESS_TOKEN)
        self.secret = options.get('secret')

    def get_code_url(self, callback_url):
        scope = 'https://cloud.feedly.com/subscriptions'
        response_type = 'code'

        request_url = '%s?client_id=%s&redirect_uri=%s&scope=%s&response_type=%s' % (
            self._get_endpoint('v3/auth/auth'),
            self.client_id,
            callback_url,
            scope,
            response_type
        )
        return request_url

    def get_access_token(self, redirect_uri, code):
        params = dict(
            client_id=self.client_id,
            client_secret=self.client_secret,
            grant_type='authorization_code',
            redirect_uri=redirect_uri,
            code=code
        )

        quest_url = self._get_endpoint('v3/auth/token')
        res = requests.post(url=quest_url, params=params)
        self.feedlyConfig.set_api_requests_remained(res.headers)
        return res.json()

    def refresh_access_token(self, refresh_token):
        """Obtain a new access token by sending a refresh token to the feedly Authorization server"""
        params = dict(
            refresh_token=refresh_token,
            client_id=self.client_id,
            client_secret=self.client_secret,
            grant_type='refresh_token',
        )
        quest_url = self._get_endpoint('v3/auth/token')
        res = requests.post(url=quest_url, params=params)
        self.feedlyConfig.set_api_requests_remained(res.headers)
        return res.json()

    def get_entry(self, access_token, entry_id):
        """tag an existing entry """
        headers = {'Authorization': 'OAuth ' + access_token}
        quest_url = self._get_endpoint('v3/entries/'  +  quote_plus(entry_id))
        # data = dict(
        #     entryId=entry_id
        # )
        res = requests.put(url=quest_url, headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.put(url=quest_url, headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)
        return res.json()

    def get_user_subscriptions(self, access_token):
        """:returns list of user subscriptions"""
        headers = {'Authorization': 'OAuth ' + access_token}
        quest_url = self._get_endpoint('v3/subscriptions')
        res = requests.get(url=quest_url, headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.get(url=quest_url, headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)
        return res.json()

    def get_user_collections(self, access_token):
        """:returns list of user collections"""
        headers = {'Authorization': 'OAuth ' + access_token}
        quest_url = self._get_endpoint('v3/collections')
        res = requests.get(url=quest_url, headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.get(url=quest_url, headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)
        return res.json()

    def get_user_tags(self, access_token):
        """:returns list of user tags"""
        headers = {'Authorization': 'OAuth ' + access_token}
        quest_url = self._get_endpoint('v3/tags')
        res = requests.get(url=quest_url, headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.get(url=quest_url, headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)
        return res.json()


    def tag_an_existing_entry(self, access_token, tag_id, entry_id):
        """tag an existing entry """
        headers = {'Authorization': 'OAuth ' + access_token}
        quest_url = self._get_endpoint('v3/tags/' +  quote_plus(tag_id))
        data = dict(
            entryId=entry_id
        )
        res = requests.put(url=quest_url, headers=headers, data=json.dumps(data))
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.put(url=quest_url, headers=headers, data=json.dumps(data))
            self.feedlyConfig.set_api_requests_remained(res.headers)
        return res

    def get_enterprise_user_tags(self, access_token):
        """:returns list of user tags"""
        headers = {'Authorization': 'OAuth ' + access_token}
        quest_url = self._get_endpoint('v3/enterprise/tags')
        res = requests.get(url=quest_url, headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.get(url=quest_url, headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)
        json = res.json()
        return json


    def get_enterprise_user_tag_info(self, access_token, tag_id):
        """:returns info about tag"""
        headers = {'Authorization': 'OAuth ' + access_token}
        quest_url = self._get_endpoint('v3/enterprise/tags')
        params = dict(
            tagId=tag_id,
        )
        res = requests.get(url=quest_url, headers=headers, params=params)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.get(url=quest_url, headers=headers, params=params)
            self.feedlyConfig.set_api_requests_remained(res.headers)
        return res.json()

    def get_feed_content(self, access_token, stream_id, unread_only=True, newer_than=None):
        """:returns contents of a feed"""
        headers = {'Authorization': 'OAuth ' + access_token}
        quest_url = self._get_endpoint('v3/streams/contents')
        params = dict(
            streamId=stream_id,
            unreadOnly=unread_only,
        )
        if newer_than:
            params['newerThan'] = newer_than
        res = requests.get(url=quest_url, params=params, headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.get(url=quest_url, params=params, headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)

        return res.json()

    def mark_article_read(self, access_token, entry_ids):
        """Mark one or multiple articles as read"""
        headers = {'content-type': 'application/json',
                   'Authorization': 'OAuth ' + access_token
                   }
        quest_url = self._get_endpoint('v3/markers')
        params = dict(
            action="markAsRead",
            type="entries",
            entryIds=entry_ids,
        )
        res = requests.post(url=quest_url, data=json.dumps(params), headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.post(url=quest_url, data=json.dumps(params), headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)

        return res

    def mark_tag_read(self, access_token, tag_ids, last_read_entry_id):
        """Mark one or multiple articles as read"""
        headers = {'content-type': 'application/json',
                   'Authorization': 'OAuth ' + access_token
                   }
        quest_url = self._get_endpoint('v3/markers')
        params = dict(
            action="markAsRead",
            type="tags",
            tagIds=tag_ids,
            lastReadEntryId=last_read_entry_id,
        )
        res = requests.post(url=quest_url, data=json.dumps(params), headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.post(url=quest_url, data=json.dumps(params), headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)

        return res

    def save_for_later(self, access_token, user_id, entry_ids):
        """Saved for later.entryIds is a list for entry id."""
        headers = {'content-type': 'application/json',
                   'Authorization': 'OAuth ' + access_token
                   }
        request_url = self._get_endpoint('v3/tags') + '/user%2F' + user_id + '%2Ftag%2Fglobal.saved'

        params = dict(
            entryIds=entry_ids
        )
        res = requests.put(url=request_url, data=json.dumps(params), headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.put(url=request_url, data=json.dumps(params), headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)

        return res

    def get_profile(self, access_token):
        """:returns user profile"""
        headers = {
            'content-type': 'application/json',
            'Authorization': 'OAuth ' + access_token
        }
        quest_url = self._get_endpoint('v3/profile')

        res = requests.post(url=quest_url, headers=headers)
        self.feedlyConfig.set_api_requests_remained(res.headers)

        if res.status_code == 401:
            update_access_token_feedly()
            res = requests.post(url=quest_url, headers=headers)
            self.feedlyConfig.set_api_requests_remained(res.headers)

        return res

    def _get_endpoint(self, path=None):
        url = "https://%s" % self.service_host
        if path is not None:
            url += "/%s" % path
        return url
