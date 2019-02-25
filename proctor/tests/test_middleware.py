from __future__ import absolute_import, unicode_literals

import mock
from unittest import TestCase

from proctor import middleware


class ProctorMiddleware(middleware.BaseProctorMiddleware):

    def get_identifiers(self, request):
        return {
            'account': request.user.username,
        }


class TestBaseProctorMiddleware(TestCase):

    def setUp(self):
        self.middleware = ProctorMiddleware()

    def test_add_proc_to_request(self):
        mock_request = mock.Mock(proc=None)

        self.middleware.process_request(mock_request)

        assert mock_request.proc.fake_proctor_test_in_settings.value is None
        assert mock_request.proc.fake_proctor_test_in_settings.group is None
