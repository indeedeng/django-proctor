"""
Provides simple implementations of Django-based caching methods.

Used by ProctorMiddleware to easily take advantage of caching.
"""

import logging

import api
import groups

logger = logging.getLogger('application.proctor.cache')


class Cacher(object):
    """
    Interface for caching implementations for Proctor assigned groups.

    Implementations must override several methods that manipulate cache_dict.
    cache_dict is an arbitrary dictionary that contains group assignments as
    well as information that Cacher needs to detect invalidation conditions.
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
            logger.debug("Proctor cache MISS (first run)")
            return None

        cache_dict = self._get_cache_dict(request, params)
        if cache_dict is None:
            logger.debug("Proctor cache MISS (absent)")
            return None

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
            logger.debug("Proctor cache HIT")
            return {key: groups.GroupAssignment(*val)
                for key, val in group_dict.iteritems()}
        else:
            logger.debug("Proctor cache MISS (invalidated)")
            self._del_cache_dict(request, params)
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

        self._set_cache_dict(request, params, cache_dict)
        logger.debug("Proctor cache SET")

    def update_matrix_version(self, api_response):
        """
        Update the last seen matrix version.

        Call this after every Proctor API call.

        This causes the cache to be invalidated if the test matrix version
        changes.
        """
        version = api_response['data']['audit']['version']

        if self.seen_matrix_version != version:
            logger.info("Proctor test matrix version changed to %d.", version)
            self.seen_matrix_version = version

    def _get_cache_dict(self, request, params):
        """
        Return the cache_dict that corresponds to ProctorParameters.
        """
        raise NotImplementedError("_get_cache_dict() must be overridden.")

    def _set_cache_dict(self, request, params, cache_dict):
        """
        Set cache_dict in the cache entry corresponding to ProctorParameters.
        """
        raise NotImplementedError("_set_cache_dict() must be overridden.")

    def _del_cache_dict(self, request, params):
        """
        Delete the cache entry corresponding to ProctorParameters.
        """
        raise NotImplementedError("_del_cache_dict() must be overridden.")


class SessionCacher(Cacher):
    """
    Cache Proctor assigned groups in the Django session.
    """

    def _get_cache_dict(self, request, params):
        return request.session.get(self._get_session_dict_key())

    def _set_cache_dict(self, request, params, cache_dict):
        request.session[self._get_session_dict_key()] = cache_dict

    def _del_cache_dict(self, request, params):
        del request.session[self._get_session_dict_key()]

    def _get_session_dict_key(self):
        """Return the key used for the request.session dict."""
        return 'proctorcache'


class VersionUpdateError(RuntimeError):
    pass
