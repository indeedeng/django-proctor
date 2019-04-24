from __future__ import absolute_import, unicode_literals

from proctor.groups import ProctorGroups, GroupAssignment


class TestProctorGroups:

    def test_string_encoding_for_valid_group(self):
        # Test valid single test case
        groups = ProctorGroups({"test_one": GroupAssignment(group="test", value=0, payload="")})
        assert groups.get_group_string_list() == ["test_one0"]

    def test_string_encoding_for_null_group(self):
        # Test unassigned group. Exercises None type comparison in py3.
        groups = ProctorGroups({"test_two": GroupAssignment(group=None, value=None, payload=None)})
        assert groups.get_group_string_list() == []

    def test_string_encoding_for_inactive_group(self):
        groups = ProctorGroups({"test_two": GroupAssignment(group=None, value=-1, payload=None)})
        assert groups.get_group_string_list() == []
