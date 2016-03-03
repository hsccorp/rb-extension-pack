from __future__ import unicode_literals

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'hscreports.views',

    url(r'^$', 'configure'),
)
