import re
import datetime
from string import capwords

from django import template
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.cache import cache
from django.db.models import F, Q
from django.shortcuts import get_object_or_404

from intellicast.models import WeatherLocation
from intellicast.utils import IntellicastLocation, IntellicastFeed, CurrentConditions

"""
Summary of Template Tags and Syntax:

get_weather_conditions as [var_name]

"""

register = template.Library()

class GetConditions(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name
        
    def render(self, context):
        
        try:
            zipcode = settings.DEFAULT_ZIP_CODE
        except AttributeError:
            return ''
        
        #Fetching Location
        cname_location = 'intellicast_location_' + zipcode
        cached_data_location = cache.get(cname_location)
        if cached_data_location:
            location = cached_data_location
        else:
            try:
                location = WeatherLocation.objects.get(zipcode=zipcode)
            except:
                try:
                    i_location = IntellicastLocation(zipcode)
                except:
                    return ''
                location = WeatherLocation.objects.create(
                    intellicast_id=i_location.location_id,
                    city=i_location.city,
                    state=i_location.state,
                    zipcode=zipcode,
                    latitude=i_location.lat,
                    longitude=i_location.lon
                )
            cache.set(cname_location, location, 60 * 60 * 24)
        
        #Fetching Conditions and Forecasts
        cname = 'intellicast_feed_data_' + zipcode
        cached_data = cache.get(cname)
        if cached_data:
            (conditions, hourly_forecasts, daily_forecasts, alerts) = cached_data
        else:
            feed = IntellicastFeed(location.intellicast_id)
            conditions, hourly_forecasts, daily_forecasts, alerts = feed.get_data()
            cache.set(cname, (conditions, hourly_forecasts, daily_forecasts, alerts), 1200)
        
        conditions_obj = CurrentConditions(
            zipcode=zipcode,
            current_temp=conditions['TempF'],
            icon_code=conditions['IconCode']
        )

        context[self.var_name] = conditions_obj
        return ''
        
@register.tag
def get_weather_conditions(parser, token):
    """
    Get the weather conditions for the current site's default zipcode.
    
    Syntax:
    {% get_current_conditions as [var_name] %}
    """
    
    args = token.split_contents()
    var_name = args[-1]
    return GetConditions(var_name)















class GetAlerts(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name
        
    def render(self, context):
        
        try:
            zipcode = settings.DEFAULT_ZIP_CODE
        except AttributeError:
            return ''
        
        #Fetching Location
        cname_location = 'intellicast_location_' + zipcode
        cached_data_location = cache.get(cname_location)
        if cached_data_location:
            location = cached_data_location
        else:
            try:
                location = WeatherLocation.objects.get(zipcode=zipcode)
            except:
                try:
                    i_location = IntellicastLocation(zipcode)
                except:
                    return ''
                location = WeatherLocation.objects.create(
                    intellicast_id=i_location.location_id,
                    city=i_location.city,
                    state=i_location.state,
                    zipcode=zipcode,
                    latitude=i_location.lat,
                    longitude=i_location.lon
                )
            cache.set(cname_location, location, 60 * 60 * 24)
                
        #Fetching Conditions and Forecasts
        cname = 'intellicast_feed_data_' + zipcode
        cached_data = cache.get(cname)
        if cached_data:
            (conditions, hourly_forecasts, daily_forecasts, alerts) = cached_data
        else:
            feed = IntellicastFeed(location.intellicast_id)
            conditions, hourly_forecasts, daily_forecasts, alerts = feed.get_data()
            cache.set(cname, (conditions, hourly_forecasts, daily_forecasts, alerts), 1200)
                
        alert_items = []
        for i, item in enumerate(alerts, 1):
            alerts_dict = alerts[i]
            
            bulletin = alerts_dict['Bulletin']
            bulletin_split = bulletin.split('/', 2)
            
            alerts_obj = (alerts_dict['Headline'], capwords(bulletin_split[2]), alerts_dict['StartTime'], alerts_dict['EndTime'], alerts_dict['Urgency'])
            
            alert_items.append(alerts_obj)
        
        

        context[self.var_name] = alert_items #conditions_obj
        return ''
        
@register.tag
def get_weather_alerts(parser, token):
    """
    Get the weather conditions for the current site's default zipcode.
    
    Syntax:
    {% get_current_conditions as [var_name] %}
    """
    
    args = token.split_contents()
    var_name = args[-1]
    return GetAlerts(var_name)


