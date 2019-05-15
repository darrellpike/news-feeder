from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
from django import forms
import requests, json
from django.core.paginator import Paginator, Page
from posts.models import User


HUBSPOT_API_KEY = '6384ea2f-48d2-4672-a92a-2d4b30a9be26'

class DeltaFirstPagePaginator(Paginator):

  def __init__(self, object_list, per_page, orphans=0,
                 allow_empty_first_page=True, **kwargs):
    self.deltafirst = kwargs.pop('deltafirst', 0)
    Paginator.__init__(self, object_list, per_page, orphans,
                 allow_empty_first_page)

  def page(self, number):
    "Returns a Page object for the given 1-based page number."
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


def create_or_update_contact_hubspot(user_id, activation_key=None):
    user = User.objects.get(id=user_id)
    endpoint = 'https://api.hubapi.com/contacts/v1/contact/createOrUpdate/email/' + user.email + '/?hapikey=' + HUBSPOT_API_KEY
    headers = {}
    headers["Content-Type"] = "application/json"
    properties = {
        "properties": [
            {
                "property": "username",
                "value": user.username
            },
            {
                "property": "email_confirmed",
                "value": user.is_active
            }
        ]
    }
    if activation_key:
        properties['properties'].append({
                "property": "conformation_url",
                "value": "https://news.viceroy.tech/accounts/activate/" + str(activation_key) + "/"
            })
    if user.first_name:
        properties['properties'].append({
                "property": "firstname",
                "value": user.first_name
            })
    if user.last_name:
        properties['properties'].append({
            "property": "lastname",
            "value": user.last_name
        })
    data = json.dumps(properties)

    r = requests.post(url=endpoint, data=data, headers=headers)

    if r.status_code == 400:
        response = json.loads(r.content)
        error = response['validationResults'][0]['error']
        if error == "PROPERTY_DOESNT_EXIST" and response['validationResults'][0]['name'] == 'email_confirmed':
            options = [
                {
                    "label": "Yes",
                    "value": True
                },
                {
                    "label": "No",
                    "value": False
                }
            ]
            create_new_property_hubspot(response['validationResults'][0]['name'], 'booleancheckbox', options=options)
            create_or_update_contact_hubspot(user_id, activation_key)
        elif error == "PROPERTY_DOESNT_EXIST" and response['validationResults'][0]['name'] == 'username':
            create_new_property_hubspot(response['validationResults'][0]['name'], 'text')
            create_or_update_contact_hubspot(user_id, activation_key)
    elif r.status_code != 200:
        raise BaseException(json.loads(r.content))
    user.userprofile.hubspot_contact = True
    user.userprofile.save()
    return r


def create_new_property_hubspot(field_name, field_type, options=None, type='string'):
    """
    Creates new property on HubSpot
    :param field_name: The name for the new property must be a string
    :param field_type: The type for the new property must be one of these:
    textarea - a <textarea> field, stores data as a string
    text - a simple text box, stores a string
    date - a datepicker field, stores a date type
    file - stores the URL location of a file. Note: The file itself must be stored separately, as the contact property cannot store the file, just the URL location of a file. Treated as a string.
    number - a number input field, stores a number value
    select - a dropdown box, uses the enumeration type
    radio - a set of radio buttons, used with the enumeration data type.
    checkbox - a set of checkboxes, used with the enumeration data type
    booleancheckbox - a single checkbox, stores "true" (as a string) if checked.
    :param options: Example:
    options = [
                {
                    "label": "Yes",
                    "value": True
                },
                {
                    "label": "No",
                    "value": False
                }
            ]
    :return: response of a request
    """
    if field_type not in ['textarea', 'text', 'date', 'file', 'number',
                          'select', 'radio', 'checkbox', 'booleancheckbox']:
        raise ValueError('Must be one of these types: textarea, text, date, file, number, '
                         'select, radio, checkbox, booleancheckbox.')

    if not isinstance(field_name, str):
        raise TypeError('Must be a string.')

    if options is None:
        options = []

    endpoint = 'https://api.hubapi.com/properties/v1/contacts/properties?hapikey=' + HUBSPOT_API_KEY
    headers = {}
    headers["Content-Type"] = "application/json"
    name = field_name
    name_formatted = name.replace('_', ' ').capitalize()

    data = json.dumps(
        {
            "name": name,
            "label": name_formatted,
            "description": "Auto property - %s" % (name_formatted),
            "groupName": "contactinformation",
            "type": type,
            "fieldType": field_type,
            "formField": False,
            "options": options
        }
    )

    r = requests.post(url=endpoint, data=data, headers=headers)

    return json.loads(r.content)


def update_contact_property_hubspot(email, property_name, value, options=None):
    """
    Updating or creating property on Hubspot.
    :param name: The property name, must be a string.
    :return: status code of a response
    """
    if not isinstance(email, str) and not isinstance(property_name, str):
        raise TypeError('Must be a string.')

    endpoint = 'https://api.hubapi.com/contacts/v1/contact/email/' + email + '/profile?hapikey=' + HUBSPOT_API_KEY
    headers = {}
    headers["Content-Type"] = "application/json"
    data = json.dumps({
        "properties": [
            {
                "property": property_name,
                "value": value
            }
        ]
    })

    r = requests.post(endpoint, data=data, headers=headers)

    if r.status_code == 400:
        field_type = 'text'
        if isinstance(value, str):
            field_type = 'text'
        elif isinstance(value, bool):
            field_type = 'booleancheckbox'
        elif isinstance(value, int):
            field_type = 'number'

        create_new_property_hubspot(property_name, field_type=field_type, options=options)
        r = requests.post(endpoint, data=data, headers=headers)

    return r.status_code