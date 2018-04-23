from django.conf.urls import patterns, url
from .views import private

urlpatterns = patterns('',
                       url(r'^private/showTestMatrix/', private.ShowTestMatrixView.as_view(), name='showtestmatrix'),
                       url(r'^private/proctor/show', private.ShowTestMatrixView.as_view(), name='proctor_showtestmatrix'),
                       url(r'^private/proctor/force/', private.ForceGroupsView.as_view(), name='forcegroups'),
                       )
