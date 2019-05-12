
"""
Template tags for working with lists of model instances which represent
trees.
"""
from __future__ import unicode_literals
from django.db.models.fields import FieldDoesNotExist
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from mptt.utils import tree_item_iterator, drilldown_tree_for_node
import operator








from django import template
# import urlparse
from django.urls import reverse

register = template.Library()

@register.filter()
def smooth_timedelta(timedeltaobj):
    """Convert a datetime.timedelta object into Days, Hours, Minutes, Seconds."""
    secs = timedeltaobj.total_seconds()
    timetot = ""
    if secs > 86400: # 60sec * 60min * 24hrs
        days = secs // 86400
        if days == 1:
            timetot += "{} day".format(int(days))
        else:
            timetot += "{} days".format(int(days))

    if secs > 3600 and secs < 86400:
        hrs = secs // 3600
        if hrs == 1:
            timetot += " {} hour".format(int(hrs))
        else:
            timetot += " {} hours".format(int(hrs))
        # secs = secs - hrs*3600

    if secs > 60 and secs < 3600:
        mins = secs // 60
        if mins == 1:
            timetot += " {} minute".format(int(mins))
        else:
            timetot += " {} minutes".format(int(mins))
        # secs = secs - mins*60

    if secs > 0 and secs < 60:
        timetot += " {} seconds".format(int(secs))
    return timetot


@register.filter
def format_count(number):
    """Format number for 10.1k"""
    if number >= 10000:
        formatted_number = float(number) / 1000
        formatted_number = str(formatted_number)[:4] + 'k'
        return formatted_number
    else:
        return number


def user_voted(item, user):
    return item.user_voted(user)

register.filter('user_voted', user_voted)


def reverse_url_post(post):
    return "https://www.plantdietlife.com"+reverse('view_post', args=(post.pk,))
    
register.filter('reverse_url_post', reverse_url_post)


@register.filter
def classname(obj):
    return obj.__class__.__name__

@register.filter
def gibberishize(text):
    """
    This is silly...we replace the blurred text with symbols to prevent google from thinking we're stealing content 
    """
    dic = {"a":"@", "b":"$", "c":"#", "d":"&", "e":"*", "f":"!", "g":"&", "h":"(",
           "i":")", "j":"=", "k":"?", "l":"&", "m":"$", "n":"~", "o":"[", "q":"]",
           "r":"/", "s":"{", "t":"}", "u":"[", "v":"]", "w":"%", "x":"#", "y":"@",
           "z":"%"
           }
    for d in dic:
        text=text.replace(d,dic[d])
        text=text.replace(d.upper(),dic[d])
    return text








### RECURSIVE TAGS

@register.filter
def cache_tree_children(queryset):
    """
    Takes a list/queryset of model objects in MPTT left (depth-first) order,
    caches the children on each node, as well as the parent of each child node,
    allowing up and down traversal through the tree without the need for
    further queries. This makes it possible to have a recursively included
    template without worrying about database queries.

    Returns a list of top-level nodes. If a single tree was provided in its
    entirety, the list will of course consist of just the tree's root node.

    """

    current_path = []
    top_nodes = []

    # If ``queryset`` is QuerySet-like, set ordering to depth-first
    if hasattr(queryset, 'order_by'):
        mptt_opts = queryset.model._mptt_meta
        tree_id_attr = mptt_opts.tree_id_attr
        left_attr = mptt_opts.left_attr
        queryset = queryset.order_by(tree_id_attr, left_attr)

    if queryset:
        # Get the model's parent-attribute name
        parent_attr = queryset[0]._mptt_meta.parent_attr
        root_level = None
        for obj in queryset:
            # Get the current mptt node level
            node_level = obj.get_level()

            if root_level is None:
                # First iteration, so set the root level to the top node level
                root_level = node_level

            if node_level < root_level:
                # ``queryset`` was a list or other iterable (unable to order),
                # and was provided in an order other than depth-first
                raise ValueError(
                    _('Node %s not in depth-first order') % (type(queryset),)
                )

            # Set up the attribute on the node that will store cached children,
            # which is used by ``MPTTModel.get_children``
            obj._cached_children = []

            # Remove nodes not in the current branch
            while len(current_path) > node_level - root_level:
                current_path.pop(-1)

            obj.score=obj.get_score()
            #obj.user_voted=obj.user_voted(request.user)
            if node_level == root_level:
                # Add the root to the list of top nodes, which will be returned
                top_nodes.append(obj)
            else:
                # Cache the parent on the current node, and attach the current
                # node to the parent's list of children
                _parent = current_path[-1]
                setattr(obj, parent_attr, _parent)
                _parent._cached_children.append(obj)

            # Add the current node to end of the current path - the last node
            # in the current path is the parent for the next iteration, unless
            # the next iteration is higher up the tree (a new branch), in which
            # case the paths below it (e.g., this one) will be removed from the
            # current path during the next iteration
            current_path.append(obj)

    return top_nodes


class RecurseTreeNode(template.Node):
    def __init__(self, template_nodes, queryset_var):
        self.template_nodes = template_nodes
        self.queryset_var = queryset_var

    def _render_node(self, context, node):
        bits = []
        context.push()
        children = node.get_children()
        children = sorted(children, key=operator.attrgetter('score'),reverse=True)
        for child in children:
            bits.append(self._render_node(context, child))
        context['node'] = node
        context['children'] = mark_safe(''.join(bits))
        rendered = self.template_nodes.render(context)
        context.pop()
        return rendered

    def render(self, context):
        queryset = self.queryset_var.resolve(context)
        roots = cache_tree_children(queryset)
        roots = sorted(roots, key=operator.attrgetter('score'),reverse=True)


        bits = [self._render_node(context, node) for node in roots]
        return ''.join(bits)


@register.tag
def recursetree(parser, token):
    """
    Iterates over the nodes in the tree, and renders the contained block for each node.
    This tag will recursively render children into the template variable {{ children }}.
    Only one database query is required (children are cached for the whole tree)

    Usage:
            <ul>
                {% recursetree nodes %}
                    <li>
                        {{ node.name }}
                        {% if not node.is_leaf_node %}
                            <ul>
                                {{ children }}
                            </ul>
                        {% endif %}
                    </li>
                {% endrecursetree %}
            </ul>
    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(_('%s tag requires a queryset') % bits[0])

    queryset_var = template.Variable(bits[1])

    template_nodes = parser.parse(('endrecursetree',))
    parser.delete_first_token()

    return RecurseTreeNode(template_nodes, queryset_var)




