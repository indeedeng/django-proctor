from __future__ import absolute_import, unicode_literals

import re

from django import template

from .. import views

register = template.Library()


@register.simple_tag(takes_context=True)
def addforcegroups(context, test_name, bucket_value):
    cleaned_groups = get_clean_groups(context, test_name)

    # add current test and assignment to list
    cleaned_groups.append('{test}{bucket}'.format(test=test_name, bucket=bucket_value))

    # flatten list back to a string
    return ','.join(cleaned_groups)


@register.simple_tag(takes_context=True)
def removeforcegroups(context, test_name):
    cleaned_groups = get_clean_groups(context, test_name)

    # flatten list back to a string
    return ','.join(cleaned_groups)


def get_clean_groups(context, test_name):
    # Look for the prforceGroups cookie and join the existing
    # and the new forced groups together
    request = context['request']
    groups = views.private.ForceGroupsView.get_prforcegroups(request)

    # split into a list a remove any entries matching the current test
    group_list = [group for group in groups.split(',') if group]
    regex = r'\b' + re.escape(test_name) + r'-?\d{0,3}\b'
    cleaned_groups = [group for group in group_list if not re.search(regex, group, re.IGNORECASE)]

    return cleaned_groups
