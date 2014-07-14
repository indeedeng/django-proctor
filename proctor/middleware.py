from django.conf import settings

import api
import groups


class ProctorMiddleware(object):
    """
    Middleware that gets all Proctor test group assignments via the REST API.

    Should be overridden to include your own context variables and identifiers.

    All requests get a ProctorGroups object, request.proc

    See the README or groups.py for details on the 'proc' object.

    Detects 'prforceGroups' in the request and sets cookies appropriately.
    """

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

        api_response = api.call_proctor(params)
        group_dict = groups.extract_groups(api_response, params.defined_tests)
        request.proc = groups.ProctorGroups(group_dict)

        return None

    def process_response(self, request, response):
        """Add prforceGroups cookie if necessary."""
        # Only necessary if user has new prforceGroups for us.
        if self.is_privileged(request) and 'prforceGroups' in request.GET:
            # Cookie lasts until end of browser session.
            # forcegroups is for dev testing, don't want it to last forever.
            response.set_cookie('prforceGroups',
                value=request.GET['prforceGroups'])
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

    def _get_force_groups(self, request):
        """
        Return the force groups string from the request after verifying it.

        Return None if there was no force groups string.

        The force groups string comes from query parameters or cookies and is
        only used if the user is privileged.
        """
        privileged = self.is_privileged(request)

        if privileged and 'prforceGroups' in request.GET:
            return request.GET['prforceGroups']
        # Even if the cookie is present, no guarantee that we set it.
        # So we must check privilege again.
        elif privileged and 'prforceGroups' in request.COOKIES:
            return request.COOKIES['prforceGroups']
        else:
            return None
