import api
import groups


def identify_groups(params, cacher=None, request=None):
    """
    Identify the groups associated with the params and return ProctorGroups.

    params: an api.ProctorParameters instance, which contains all the
        values important for group assignment like identifiers.
    cacher: If provided, use this cache.Cacher instance to cache all API calls.
        Reduces the number of HTTP requests to the Proctor API. (default: None)
    request: The Django request. Only used if cacher is a cache.SessionCacher.
        (default: None)

    You can access test group assignments through the dot operator on the
    returned ProctorGroups:

    >>> proc.buttoncolortst
    GroupAssignment(group=u'blue', value=1, payload=u'#2B60DE')

    See groups.py or the README for more details.
    """
    return groups.ProctorGroups(load_group_dict(params, cacher, request))


def load_group_dict(params, cacher=None, request=None):
    group_dict = None
    if cacher is not None:
        group_dict = cacher.get(request, params)
    if group_dict is None:
        # Cache miss or caching disabled.
        api_response = api.call_proctor(params)
        group_dict = groups.extract_groups(api_response, params.defined_tests)
        # Must cache the api response, but not if api had an error.
        if cacher is not None and api_response is not None:
            cacher.update_matrix_version(api_response)
            cacher.set(request, params, group_dict)

    return group_dict
