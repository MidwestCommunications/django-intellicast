from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('intellicast.views',
    
    url(r'^$',
        'weather_page',
        name='intellicast_weather_page'
    ),
    
    #url(r'^forecast/$',
    #    'daily_weather_detail',
    #    name='intellicast_daily_weather_detail'
    #),
    
    url(r'^forecast/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$',
        'daily_weather_detail',
        name='intellicast_daily_weather_detail'
    ),

    url(r'^texting/$',
        'texting_weather',
        name='intellicast_texting_weather'
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