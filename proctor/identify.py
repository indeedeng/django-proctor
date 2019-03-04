from __future__ import absolute_import, unicode_literals

from django.conf import settings

from . import api
from . import groups
from . import lazy as lazy_groups


def identify_groups(params, cacher=None, request=None, lazy=False, http=None):
    """
    Identify the groups associated with the params and return ProctorGroups.

    params: an api.ProctorParameters instance, which contains all the
        values important for group assignment like identifiers.
    cacher: If provided, use this cache.Cacher instance to cache all API calls.
        Reduces the number of HTTP requests to the Proctor API. (default: None)
    request: The Django request. Only used if cacher is a cache.SessionCacher.
        (default: None)
    http: An instance of requests.Session (or equivalent), used for making
        http requests (default: None)
    lazy: A bool indicating whether group assignment should be lazy. If True,
        cache lookup and HTTP requests to the Proctor API are delayed until
        the group assignments are accessed for the first time. (default: False)

    You can access test group assignments through the dot operator on the
    returned ProctorGroups:

    >>> proc.buttoncolortst
    GroupAssignment(group=u'blue', value=1, payload=u'#2B60DE')

    See groups.py or the README for more details.
    """
    if lazy:
        return lazy_groups.LazyProctorGroups(params, cacher, request, http)
    else:
        return groups.ProctorGroups(load_group_dict(params, cacher, request, http))


def load_group_dict(params, cacher=None, request=None, http=None):
    group_dict = None
    if cacher is not None:
        group_dict = cacher.get(request, params)
    if group_dict is None:
        # Cache miss or caching disabled.
        api_response = api.call_proctor_identify(params, http=http)
        if api_response:
            group_dict = groups.extract_groups(api_response, params.defined_tests)
        else:
            # If api request failed, attempt to force load from cache
            group_dict = (cacher.get(request, params, allow_expired=True) if cacher else None
                          or groups.extract_groups(None, params.defined_tests))

        # Must cache the api response, but not if api had an error.
        if cacher is not None and api_response is not None:
            cacher.set(request, params, group_dict, api_response)

    return group_dict


def proc_by_accountid(accountid):
    """ Gets proctor groups by accountid

    Args:
        accountid: typically the same id found in request.user.username

    Returns:
        GroupAssignment
    """
    identifier = {'account': accountid}
    params = api.ProctorParameters(
                api_root=settings.PROCTOR_API_ROOT,
                defined_tests=settings.PROCTOR_TESTS,
                context_dict={'ua': ''},
                identifier_dict=identifier,
                force_groups=None,
            )
    return identify_groups(params)
