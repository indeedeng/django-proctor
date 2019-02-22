"""
Provide a convenient way of accessing test groups with the dot operator.

Proctor API responses typically add a 'proc' attribute to the request object.
This 'proc' attribute is a ProctorGroups object.

ProctorGroups allows access to the group assignments of all test names provided
by defined_tests (typically PROCTOR_TESTS in the Django settings) through the
dot operator. Attempting to access a test not in PROCTOR_TESTS throw an
AttributeError. (Django templates interpret this error as a blank string.)

>>> request.proc.buttoncolortst
GroupAssignment(group=u'blue', value=1, payload=u'#2B60DE')

>>> request.proc.testnotinsettings
AttributeError

Each assignment has three attributes: group, value, and payload.

group: the assigned test group name. (str)
value: the assigned bucket value. (int)
    -1 typically means inactive, and 0 typically means control.
payload: the assigned test group payload value.
    used to change test-specific values from Proctor instead of in code.
    is None if the test has no payload.
    the payload type can be a str, long, double, or a list of one of those.

If Proctor did not give an assignment for a test, then that test is unassigned.
In that case: group, value, and payload are all None.

>>> request.proc.buttoncolortst
GroupAssignment(group=None, value=None, payload=None)

This can happen if an eligibility rule was not met, if there was no matching
identifier for the test type, if the Proctor API did not recognize the test
name, or if the API had a fatal error and set all assignments to unassigned by
default.

ALWAYS USE DEFAULT BEHAVIOR FOR THE ELSE BRANCH WHEN SWITCHING BETWEEN
DIFFERENT TEST GROUPS. This ensures reasonable default behavior if the test is
suddenly removed from the test matrix, or if the Proctor API goes down. Often,
your else branch can cover inactive, control, and None (unassigned).

    if request.proc.buttoncolortst.group == 'blue':
        ...
    elif request.proc.buttoncolortst.group == 'green':
        ...
    else:
        # control, inactive, and unassigned (all default grey)
        # Because this covers unassigned, this will be used in case of error.
        ...

When using payloads in templates, remember that the payload can be None if the
test is unassigned. In Django, if None is output from a variable tag, 'None' is
placed into the template. To avoid this, cover all payloads with a
default_if_none filter. This is typically the same text as inactive/control.

    <button>{{ proc.buttontexttst.payload|default_if_none:"Sign Up" }}</button>
"""
from __future__ import absolute_import, unicode_literals

import collections

import six


GroupAssignment = collections.namedtuple(
    'GroupAssignment', 'group value payload')

_UNASSIGNED_GROUP = GroupAssignment(group=None, value=None, payload=None)


class ProctorGroups(object):
    """
    Convenience object for accessing test groups using the dot operator.

    All test names provided to defined_tests in extract_groups() are
    guaranteed to exist as attributes of this object.
    """

    def __init__(self, group_dict):
        self._group_dict = group_dict

        # For convenience, we allow all defined tests to be accessed through
        # the dot operator on ProctorGroups.
        for test_name, assignment in six.iteritems(group_dict):
            # Make sure this doesn't overwrite an already-defined method.
            if not hasattr(self, test_name):
                setattr(self, test_name, assignment)

    def __str__(self):
        """
        Return a string of comma-separated tests with bucket values.

        Typically used for logging which test groups a request was part of for
        use in A/B testing metrics.

        Negative bucket values are ignored as those are considered inactive.

        >>> str(request.proc)
        "buttoncolortst1,countryalgotst0,newfeaturerollout0"

        """
        return ','.join(self.get_group_string_list())

    def get_group_string_list(self):
        """
        Return list of group strings which are: {testname}{bucketvalue}

        >>> request.proc.get_group_string_list()
        ['buttoncolortst1', 'countryalgotst0', 'newfeaturerollout0']

        See get_group_string(). This method is before joining with commas.

        This method is useful if you'd like to add additional
        non-Proctor-related groups before passing this list to your logger.
        """
        return [test_name + str(assignment.value)
                for test_name, assignment in six.iteritems(self._group_dict)
                if assignment is not _UNASSIGNED_GROUP and assignment.value >= 0]


def extract_groups(api_response, defined_tests):
    """
    Create and return a dict of test name to GroupAssignment.

    If api_response is None, return a dict with a None-like object for every
    defined test. This guarantees that all defined_tests exist if the REST API
    had an error.

    api_response: the JSON response from the Proctor API in Python object form.
    defined_tests: an iterable of test name strings defining the tests that
        should be available to the user. Usually from Django settings.
    """
    if api_response is None:
        return {test_name: _UNASSIGNED_GROUP for test_name in defined_tests}

    api_groups = api_response['data']['groups']
    group_dict = {}
    for test_name in defined_tests:
        if test_name in api_groups:
            bucket_fields = api_groups[test_name]
            # payload is hidden behind one of 'stringValue', 'longArray', etc.
            # Sometimes there is no payload.
            payload = (bucket_fields['payload'].popitem()[1]
                       if 'payload' in bucket_fields else None)
            assignment = GroupAssignment(group=bucket_fields['name'],
                                         value=bucket_fields['value'], payload=payload)
            group_dict[test_name] = assignment
        else:
            # The API doesn't include a response for unassigned tests.
            # For all valid tests, we use a dummy object with None attributes.
            # For tests NOT in the settings, access is an AttributeError.
            # This helps enforce program correctness.
            group_dict[test_name] = _UNASSIGNED_GROUP

    return group_dict
