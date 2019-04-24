from __future__ import absolute_import, unicode_literals

import pytest

from proctor.groups import ProctorGroups, GroupAssignment


class TestProctorGroups:

    def test_string_encoding(self):
        # Test valid single test case
        groups = ProctorGroups({"test_one": GroupAssignment(group="test", value=0, payload="")})
        assert groups.get_group_string_list() == ["test_one0"]

        # Test unassigned group. Exercises None type comparison in py3.
        groups = ProctorGroups({"test_two": GroupAssignment(group=None, value=None, payload=None)})
        assert groups.get_group_string_list() == []
