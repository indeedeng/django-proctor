from __future__ import absolute_import, unicode_literals

from unittest import TestCase
from mock import Mock

from proctor.middleware import BaseProctorMiddleware


class ProctorMiddleware(BaseProctorMiddleware):
    def get_identifiers(self, request):
        return {
            'account': request.user.username,
        }


class TestBaseProctorMiddleware(TestCase):

    def setUp(self):
        self.middleware_class = ProctorMiddleware
        self.middleware = self.middleware_class()

    def test_add_proc_to_request(self):
        mock_request = Mock(proc=None)

        self.middleware.process_request(mock_request)

        assert mock_request.proc.fake_proctor_test_in_settings.value is None
        assert mock_request.proc.fake_proctor_test_in_settings.group is None

    def test_middleware_object_is_callable(self):
        """Assert object created from middleware class is callable.

        Note that `get_response` only gets called if view called by request return None,
        so by default `assert_get_response_called` is False.
        """
        # New-style middleware is initialized with a get-response callback.
        # See https://docs.djangoproject.com/en/2.2/topics/http/middleware/
        get_response_callback = Mock()
        middleware = self.middleware_class(get_response_callback)
        request = Mock()
        try:
            middleware(request)
        except TypeError as error:
            if not str(error).endswith("takes no parameters"):
                raise
            msg = self.middleware_class.__name__ + " cannot be called with request object"
            raise AssertionError(msg)

        get_response_callback.assert_called_once_with(request)
