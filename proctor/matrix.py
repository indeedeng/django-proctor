from __future__ import absolute_import, unicode_literals

from proctor import api


def identify_matrix(params, cacher=None, request=None, http=None):
    """
    Identify the tests associated with the params and return the Proctor Test Matrix.

    params: an api.ProctorParameters instance, which contains all the
        values important for test identification.
    cacher: If provided, use this cache.Cacher instance to cache all API calls.
        Reduces the number of HTTP requests to the Proctor API. (default: None)
    request: The Django request. Only used if cacher is a cache.SessionCacher.
        (default: None)
    http: An instance of requests.Session (or equivalent), used for making
        http requests (default: None)

    """
    test_dict = None
    if cacher is not None:
        test_dict = cacher.get(request, params)
    if test_dict is None:
        # Cache miss or caching disabled.
        api_response = api.call_proctor_matrix(params, http=http)
        test_dict = extract_tests(api_response, params.defined_tests)
        # Must cache the api response, but not if api had an error.
        if cacher is not None and api_response is not None:
            cacher.set(request, params, test_dict, api_response)

    return test_dict


def extract_tests(api_response, defined_tests):
    """
    Create and return a dict of test name to test data.

    If api_response is None, return a dict with an empty dict.

    api_response: the JSON response from the Proctor API in Python object form.
    defined_tests: an iterable of test name strings defining the tests that
        should be available to the user. Usually from Django settings.
    """
    if api_response is None:
        return {'tests': {}}

    api_audit = api_response['audit']
    api_tests = api_response['tests']
    test_dict = {}
    for test_name in defined_tests:
        if test_name in api_tests:
            test_dict[test_name] = api_tests[test_name]
        else:
            # For all valid tests, we use an empty dict.
            # For tests NOT in the settings, access is an AttributeError.
            # This helps enforce program correctness.
            test_dict[test_name] = {}

    return {'audit': api_audit, 'tests': test_dict}
