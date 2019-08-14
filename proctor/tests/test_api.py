from __future__ import absolute_import, unicode_literals

import mock

from proctor import api, constants
from proctor.tests.utils import create_proctor_parameters


class TestApi:
    def test_api_timeout(self):
        with mock.patch.object(api, 'requests') as mocked_requests:
            params = create_proctor_parameters({})

            mocked_requests.get.side_effect = Exception(mock.Mock(status=408), 'request timed out')

            try:
                api.call_proctor(params, http=mocked_requests)
                assert False

            except Exception:
                assert mocked_requests.get.call_count == constants.MAX_HTTP_RETRIES

    def test_api_no_timeout(self):
        with mock.patch.object(api, 'requests') as mocked_requests:
            params = create_proctor_parameters({})

            api.call_proctor(params, http=mocked_requests)
            assert mocked_requests.get.call_count == 1
