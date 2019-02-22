from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from .views import private


urlpatterns = [
   url(r'^showTestMatrix/', private.ShowTestMatrixView.as_view(), name='showtestmatrix'),
   url(r'^proctor/show', private.ShowTestMatrixView.as_view(), name='proctor_showtestmatrix'),
   url(r'^proctor/force/', private.ForceGroupsView.as_view(), name='forcegroups'),
]
