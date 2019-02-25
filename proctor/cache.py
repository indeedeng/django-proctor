"""
Provides simple implementations of Django-based caching methods.

Used by ProctorMiddleware to easily take advantage of caching.
"""
from __future__ import absolute_import, unicode_literals

import logging
import string
import time

import django.core.cache
import six

from . import api
from . import groups

logger = logging.getLogger('application.proctor.cache')


class Cacher(object):
    """
    Interface for caching implementations for Proctor assigned groups.

    Implementations must override several methods that manipulate cache_dict.
    cache_dict is an arbitrary dictionary that contains group assignments as
    well as information that Cacher needs to detect invalidation conditions.
    """
    def __init__(self, version_timeout_seconds=None):
        """
        version_timeout_seconds: The Pipet API will be queried to check for a
            new matrix version at least this often. Default: 5 minutes
        """
        self.version_timeout_seconds = (version_timeout_seconds
                                        if version_timeout_seconds is not None
                                        else (5 * 60))

    def get(self, request, params, allow_expired=False):
        """
        Return the cached group_dict for the given ProctorParameters.

        Return None if there was nothing in the cache or if the cached dict
        is now invalid.
        """
        latest_seen_version = self._get_latest_version()
        if latest_seen_version is None:
            # App hasn't seen any matrix versions yet or it expired.
            logger.debug("Proctor cache MISS (version expired)")
            return None

        cache_dict = self._get_cache_dict(request, params)
        if cache_dict is None:
            logger.debug("Proctor cache MISS (absent)")
            return None

        group_dict = cache_dict['group_dict']
        cache_params = api.ProctorParameters(**cache_dict['params'])
        cache_matrix_version = cache_dict['matrix_version']

        # Make sure cache is invalidated if something changes.
        # If the test matrix changed, then assignments may have changed.
        # Parameters like forcegroups might change assignments too.
        valid = (cache_matrix_version == latest_seen_version and params == cache_params)
        if valid:
            # ProctorGroups is a namedtuple serialized into a dict for JSON.
            # Need to convert it back before returning.
            logger.debug("Proctor cache HIT")
            return {key: groups.GroupAssignment(*val)
                    for key, val in six.iteritems(group_dict)}
        else:
            logger.debug("Proctor cache MISS (invalidated)")
            self._del_cache_dict(request, params)
            return None

    def set(self, request, params, group_dict, api_response):
        """
        Cache the group_dict associated with the given ProctorParameters.

        You MUST call update_matrix_version() before calling this method.
        """
        latest_seen_version = self.update_matrix_version(api_response)

        cache_dict = {}
        cache_dict['group_dict'] = group_dict
        cache_dict['params'] = params.as_dict()
        cache_dict['matrix_version'] = latest_seen_version

        self._set_cache_dict(request, params, cache_dict)
        logger.debug("Proctor cache SET")

    def update_matrix_version(self, api_response):
        """
        Update the last seen matrix version.

        Return the last seen matrix version (for convenience).

        Call either set() or this after every Proctor API call.
        (set calls this for you.)

        This causes the cache to be invalidated if the test matrix version
        changes.
        """
        new_version = api_response['data']['audit']['version']
        latest_seen_version = self._get_latest_version()

        # Set cache unconditionally.
        # This resets our timeout for re-checking the Proctor API.
        self._set_latest_version(new_version)

        if latest_seen_version != new_version:
            logger.debug("Proctor test matrix version changed to %s.", new_version)
            latest_seen_version = new_version

        return latest_seen_version

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

    def _get_latest_version(self):
        """
        Return the most recently seen matrix version.

        Return None if no matrix version has been seen before, or if version
        seen has exceeded the version timeout.
        """
        raise NotImplementedError("_get_latest_version() must be overridden.")

    def _set_latest_version(self, version):
        """
        Set the most recently seen matrix version.
        """
        raise NotImplementedError("_set_latest_version() must be overridden.")


class SessionCacher(Cacher):
    """
    Cache Proctor assigned groups in the Django session.
    """
    def __init__(self, version_timeout_seconds=None):
        super(SessionCacher, self).__init__(version_timeout_seconds)

        # Store last seen here since sessions have no all-process storage.
        # This variable is PER-PROCESS!
        self.seen_matrix_version = None
        self.version_expiry_time = time.time()

    def get(self, request, params, allow_expired=False):
        if allow_expired:
            self.version_expiry_time = time.time() + self.version_timeout_seconds
        return super(SessionCacher, self).get(request, params)

    def _get_cache_dict(self, request, params):
        return request.session.get(self._get_session_dict_key())

    def _set_cache_dict(self, request, params, cache_dict):
        request.session[self._get_session_dict_key()] = cache_dict

    def _del_cache_dict(self, request, params):
        del request.session[self._get_session_dict_key()]

    def _get_latest_version(self):
        if time.time() >= self.version_expiry_time:
            # Last seen version has expired. Force recheck of test matrix.
            return None
        else:
            return self.seen_matrix_version

    def _set_latest_version(self, version):
        self.seen_matrix_version = version
        self.version_expiry_time = time.time() + self.version_timeout_seconds

    def _get_session_dict_key(self):
        """Return the key used for the request.session dict."""
        return 'proctorcache'


class CacheCacher(Cacher):
    """
    Cache Proctor assigned groups using Django's cache framework.

    To determine the cache key, the cacher combines all the identifiers
    together. This is likely to stay the same across requests.

    If you run into CacheKeyWarnings due to length, you may need to subclass
    this and use a different cache key strategy, like using only one identifier
    or using a hash().

    CacheCacher uses the timeout from your Django settings (5 min by default).
    But Cacher handles cache invalidation well, so you can increase this to
    as long as forever if you want.
    """

    # Memcached disallows spaces, newlines, etc. It treats colons specially
    # for stats, and we use pipes to separate identifiers.
    _VALID_KEY_CHARS = (
        frozenset(string.ascii_letters + string.digits + string.punctuation) -
        frozenset(':|')
    )

    def __init__(self, cache_name=None, version_timeout_seconds=None):
        super(CacheCacher, self).__init__(version_timeout_seconds)
        cache_name = cache_name or 'default'
        self.cache = django.core.cache.caches[cache_name]

    def _get_cache_dict(self, request, params):
        return self.cache.get(self._get_cache_key(params))

    def _set_cache_dict(self, request, params, cache_dict):
        self.cache.set(self._get_cache_key(params), cache_dict)

    def _del_cache_dict(self, request, params):
        self.cache.delete(self._get_cache_key(params))

    def _get_latest_version(self):
        return self.cache.get(self._get_cache_version_key(), None)

    def _set_latest_version(self, version):
        self.cache.set(self._get_cache_version_key(), version,
                       timeout=self.version_timeout_seconds)

    def _get_cache_key(self, params):
        prefix = self._get_cache_prefix()
        ident_dict = params.identifier_dict

        # Sort values by identifier name (must be consistent).
        idents = (str(value) for key, value in sorted(ident_dict.items()))
        # Get rid of bad control characters like spaces.
        # And concatenate ids with pipes (for sanity when debugging caching).
        filtered_id_string = '|'.join(
            ''.join(char for char in ident if char in self._VALID_KEY_CHARS)
            for ident in idents)
        return ':'.join([prefix, filtered_id_string])

    def _get_cache_prefix(self):
        return 'proc'

    def _get_cache_version_key(self):
        return self._get_cache_prefix() + 'version'
