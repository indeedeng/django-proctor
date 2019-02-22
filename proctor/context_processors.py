from __future__ import absolute_import, unicode_literals


def proc(request):
    """
    Place the ProctorGroups 'proc' object in every template context.

    This makes using Proctor test groups in templates very convenient.

    Dependent on the Proctor middleware.

        {{ proc.buttoncolortst.payload|default_if_none:"..." }}

        {% if proc.buttoncolortst.group == 'green' %}
    """

    # If ProctorMiddleware failed to run, request.proc won't exist.
    return {'proc': request.proc} if hasattr(request, 'proc') else {}
