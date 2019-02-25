from __future__ import absolute_import, unicode_literals

import json

import six
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views import generic
from django.shortcuts import render

from .. import api, constants, matrix, settings as local_settings


class ShowTestMatrixView(generic.View):
    """
    Django view that displays the test matrix from Proctor.

    Only the tests defined in settings.PROCTOR_TESTS will be shown.

    Simply add this view to your urls.py like so:
        url(r'^private/', include('proctor.urls'))
    """

    def get(self, request):
        """
        Return a json representation of all proctor tests
        contained within PROCTOR_TESTS
        """
        if not request.is_privileged:
            raise Http404

        params = api.ProctorParameters(
            api_root=settings.PROCTOR_API_ROOT,
            defined_tests=settings.PROCTOR_TESTS,
            context_dict={},
            identifier_dict={},
            force_groups=None,
        )

        data = matrix.identify_matrix(params, request=request)

        json_data = json.dumps(data, indent=2, separators=(',', ': '))
        return HttpResponse(json_data, content_type='application/json;charset=UTF-8')


class ForceGroupsView(generic.TemplateView):
    template_name = "proctor_groups.html"

    def get(self, request, *args, **kwargs):
        """
        Shows which groups you're in.
        Allows you to force into any of the groups.
        """
        params = api.ProctorParameters(
            api_root=settings.PROCTOR_API_ROOT,
            defined_tests=settings.PROCTOR_TESTS,
            context_dict={},
            identifier_dict={},
            force_groups=None,
        )
        test_matrix = matrix.identify_matrix(params, request=request)

        your_groups = {test_name: assignment.value
                       for test_name, assignment in six.iteritems(request.proc._group_dict)}

        prforcegroups = self.get_prforcegroups(request)

        allocations = {}
        for test in settings.PROCTOR_TESTS:
            assignment_value = your_groups.get(test, -5)
            assignment_fullname = "{test}{value}".format(test=test, value=assignment_value)
            single_test_matrix = test_matrix["tests"].get(test, {})
            test_allocations = single_test_matrix.get("allocations", [])
            test_buckets = single_test_matrix.get("buckets", [])
            iter_test_ranges = next(iter(test_allocations), {}).get('ranges', [])
            test_ranges = self._get_test_ranges(iter_test_ranges, test_buckets)

            allocations[test] = {
                "buckets": test_buckets,
                "ranges": test_ranges,
                "assignment": assignment_value,
                "forced": assignment_fullname in prforcegroups
            }

        context = {
            "allocations": allocations,
            "basetemplate": self._get_base_template()
        }
        return render(request, self.template_name, context)

    def _get_test_ranges(self, ranges, buckets):
        bucket_dict = {}
        for idx, bucket in enumerate(buckets):
            bucket_dict.update({bucket['value']: {'name': bucket['name'], 'index': idx}})

        for test_range in ranges:
            bucket = bucket_dict[test_range['bucketValue']]
            test_range['name'] = bucket['name']
            test_range['index'] = bucket['index']
            test_range['percentage'] = test_range['length'] * 100

        return ranges

    def _get_base_template(self):
        if hasattr(settings, 'PROCTOR_BASE_TEMPLATE'):
            return settings.PROCTOR_BASE_TEMPLATE
        else:
            return local_settings.PROCTOR_BASE_TEMPLATE

    @staticmethod
    def get_prforcegroups(request):
        # get the prforcegroups information from the cookie or the url params
        # since this code is hit before the middleware sets the cookie, url params
        # will take precedence
        prforcegroups = request.GET.get(constants.PROP_NAME_FORCE_GROUPS, None)
        if prforcegroups is None:
            prforcegroups = request.COOKIES.get(constants.PROP_NAME_FORCE_GROUPS, '')

        return prforcegroups
