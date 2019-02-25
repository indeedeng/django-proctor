from __future__ import absolute_import, unicode_literals

import six
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from . import api
from . import cache
from . import identify
from . import constants


class BaseProctorMiddleware(object):
    """
    Middleware that gets all Proctor test group assignments via the REST API.

    Should be overridden to include your own context variables and identifiers.

    All requests get a ProctorGroups object, request.proc

    See the README or groups.py for details on the 'proc' object.

    Detects 'prforceGroups' in the request and sets cookies appropriately.
    """

    def __init__(self):
        self.cacher = self.get_cacher()

        if isinstance(settings.PROCTOR_TESTS, six.string_types):
            # User accidentally defined a string instead of tuple in settings.
            # PROCTOR_TESTS = (
            #     'buttoncolortst'
            # )
            raise ImproperlyConfigured(
                "PROCTOR_TESTS should be a tuple or list, not a string. "
                "When defining a tuple, make sure you include a comma: "
                "PROCTOR_TESTS = ('mytest',)"
            )

    def process_request(self, request):
        """
        Call the Proctor API and obtain all test group assignments.

        Group assignments are placed into request.proc for other Django apps.
        """
        params = api.ProctorParameters(
            api_root=settings.PROCTOR_API_ROOT,
            defined_tests=settings.PROCTOR_TESTS,
            context_dict=self.get_context(request),
            identifier_dict=self.get_identifiers(request),
            force_groups=self._get_force_groups(request),
        )

        request.proc = identify.identify_groups(
            params, cacher=self.cacher, request=request, lazy=self.is_lazy(), http=self.get_http())

        return None

    def process_response(self, request, response):
        """Add prforceGroups cookie if necessary."""
        # Only necessary if user has new prforceGroups for us.
        if self.is_privileged(request) and constants.PROP_NAME_FORCE_GROUPS in request.GET:
            # Cookie lasts until end of browser session.
            # forcegroups is for dev testing, don't want it to last forever.
            response.set_cookie(constants.PROP_NAME_FORCE_GROUPS,
                                value=request.GET[constants.PROP_NAME_FORCE_GROUPS])
        return response

    def get_context(self, request):
        """
        Return the context variables for a given request as a dict.

        Override to use your own context variables.

        By default, an empty dict is returned. However, most applications will
        want to use Proctor rules to enhance their tests with contexts like
        user agent and country.
        """
        return {}

    def get_identifiers(self, request):
        """
        Return the identifiers for a given request as a dict.

        Override to use your own identifiers. At least one must exist.

        Examples of identifiers include tracking cookies and account ids.
        """
        raise NotImplementedError("get_identifiers must be overridden.")

    def is_privileged(self, request):
        """
        Return a bool indicating whether the request is privileged.

        Used to determine whether to trust prforceGroups query parameters and
        cookies.

        Override with your own privilege determination method. By default, this
        returns False, which effectively disables prforceGroups.

        Privilege is typically defined as a trusted IP from your office, but
        this can be determined by other factors like admin account as well.
        """
        return False

    def get_cacher(self):
        """
        Create a cacher based on the PROCTOR_CACHE_METHOD Django setting.
        """
        cache_method = getattr(settings, 'PROCTOR_CACHE_METHOD', None)

        if cache_method is None:
            return None
        elif cache_method == 'session':
            return cache.SessionCacher()
        elif cache_method == 'cache':
            cache_name = getattr(settings, 'PROCTOR_CACHE_NAME', None)
            return cache.CacheCacher(cache_name)
        else:
            raise ImproperlyConfigured(
                "{0} is an unrecognized PROCTOR_CACHE_METHOD.".format(
                    cache_method))

    def is_lazy(self):
        return getattr(settings, 'PROCTOR_LAZY', False)

    def get_http(self):
        """
        Return an instance of requests.Session (or equivalent) that will be
        used to make HTTP requests to the proctor API.

        Return None to not use a session (e.g. requests.get).

        This method is called every time process_request is called.
        """
        return None

    def _get_force_groups(self, request):
        """
        Return the force groups string from the request after verifying it.

        Return None if there was no force groups string.

        The force groups string comes from query parameters or cookies and is
        only used if the user is privileged.
        """
        privileged = self.is_privileged(request)

        if privileged and constants.PROP_NAME_FORCE_GROUPS in request.GET:
            return request.GET[constants.PROP_NAME_FORCE_GROUPS]
        # Even if the cookie is present, no guarantee that we set it.
        # So we must check privilege again.
        elif privileged and constants.PROP_NAME_FORCE_GROUPS in request.COOKIES:
            return request.COOKIES[constants.PROP_NAME_FORCE_GROUPS]
        else:
            return None
