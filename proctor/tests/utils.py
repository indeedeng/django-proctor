from django.conf import settings


from proctor import api


def create_proctor_parameters(identifier_dict, defined_tests=None):
    if defined_tests is None:
        defined_tests = settings.PROCTOR_TESTS

    params = api.ProctorParameters(
        api_root=settings.PROCTOR_API_ROOT,
        defined_tests=defined_tests,
        context_dict={'ua': ''},
        identifier_dict=identifier_dict,
        force_groups=None,
    )
    return params
