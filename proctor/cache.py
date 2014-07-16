"""
Provides simple implementations of Django-based caching methods.

Used by ProctorMiddleware to easily take advantage of caching.
"""

import api
import groups


class SessionCacher(object):
    """
    Cache Proctor assigned groups in the session.
    """
    def __init__(self):
        self.seen_matrix_version = None

    def get(self, request, params):
        """
        Return the cached group_dict for the given ProctorParameters.

        Return None if there was nothing in the cache or if the cached dict
        is now invalid.
        """
        if self.seen_matrix_version is None:
            # On the first get(), we've seen no version, so we can't use the
            # cache yet.
            return None

        proctor_key = self.get_session_dict_key()
        if proctor_key not in request.session:
            return None

        cache_dict = request.session[proctor_key]
        group_dict = cache_dict['group_dict']
        cache_params = api.ProctorParameters(**cache_dict['params'])
        matrix_version = cache_dict['matrix_version']

        # Make sure cache is invalidated if something changes.
        # If the test matrix changed, then assignments may have changed.
        # Parameters like forcegroups might change assignments too.
        valid = (matrix_version == self.seen_matrix_version and
            params == cache_params)
        if valid:
            # ProctorGroups is a namedtuple serialized into a dict for JSON.
            # Need to convert it back before returning.
            return {key: groups.GroupAssignment(*val)
                for key, val in group_dict.iteritems()}
        else:
            del request.session[proctor_key]
            return None

    def set(self, request, params, group_dict):
        """
        Cache the group_dict associated with the given ProctorParameters.

        You MUST call update_matrix_version() before calling this method.
        """
        if self.seen_matrix_version is None:
            raise VersionUpdateError(
                "update_matrix_version() must be called before set().")

        cache_dict = {}
        cache_dict['group_dict'] = group_dict
        cache_dict['params'] = params.as_dict()
        cache_dict['matrix_version'] = self.seen_matrix_version
        request.session[self.get_session_dict_key()] = cache_dict

    def update_matrix_version(self, api_response):
        """
        Update the last seen matrix version.

        Call this after every Proctor API call.

        This causes the cache to be invalidated if the test matrix version
        changes.
        """
        version = api_response['data']['audit']['version']
        self.seen_matrix_version = version

    def get_session_dict_key(self):
        """Return the key used for the request.session dict."""
        return 'proctorcache'


class VersionUpdateError(RuntimeError):
    pass
