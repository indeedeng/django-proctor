import groups
import identify


class LazyProctorGroups(groups.ProctorGroups):
    """
    A lazy ProctorGroups that doesn't load anything until the first usage.

    Specifically, the first load will be done when an attribute of a
    GroupAssignment is accessed or when the group string list is requested.
    """

    def __init__(self, params, cacher=None, request=None):
        self.loaded = False
        self._params = params
        self._cacher = cacher
        self._request = request
        group_dict = {test: LazyGroupAssignment(self, test)
            for test in params.defined_tests}
        super(LazyProctorGroups, self).__init__(group_dict)

    def get_group_string_list(self):
        self.load()
        return super(LazyProctorGroups, self).get_group_string_list()

    def load(self):
        if self.loaded:
            # Don't double-load.
            return

        self._group_dict = identify.load_group_dict(
            self._params, self._cacher, self._request)
        for test_name, assignment in self._group_dict.iteritems():
            # Don't overwrite anything we don't mean to.
            if isinstance(getattr(self, test_name), LazyGroupAssignment):
                setattr(self, test_name, assignment)
        self.loaded = True


class LazyGroupAssignment(object):

    def __init__(self, lazy_groups, test_name):
        self._lazy_groups = lazy_groups
        self._test_name = test_name

    def _load(self):
        self._lazy_groups.load()

    @property
    def group(self):
        self._load()
        return getattr(self._lazy_groups, self._test_name).group

    @property
    def value(self):
        self._load()
        return getattr(self._lazy_groups, self._test_name).value

    @property
    def payload(self):
        self._load()
        return getattr(self._lazy_groups, self._test_name).payload
