from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('intellicast.views',
    
    url(r'^$',
        'weather_page',
        name='intellicast_weather_page'
    ),

    #url(r'^articles/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$',
    #    'article_detail',
    #    name='scoop_article_detail'
    #),

    #url(r'^articles/(?P<article_id>\d+)/$',
    #    'article_detail',
    #    name='scoop_article_detail_byid'
    #),
    
)