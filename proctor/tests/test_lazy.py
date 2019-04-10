from __future__ import absolute_import, unicode_literals

from mock import patch
import pytest

from proctor.lazy import LazyProctorGroups
from proctor.tests.utils import create_proctor_parameters


class TestLazyProctorGroups:

    @patch('proctor.identify.load_group_dict')
    def test_lazy_proctor_groups_load_with_none_dict(self, mock_load_group_dict):
        mock_load_group_dict.return_value = None
        params = create_proctor_parameters({'account': 1234}, defined_tests=['fake_proctor_test'])
        lazy_proctor_groups = LazyProctorGroups(params)
        try:
            lazy_proctor_groups.load()
        except AttributeError:
            pytest.fail("Attribute error thrown on proctor group load when loading with self._group_dict == None")
