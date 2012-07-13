import re
import datetime
import string
import socket

socket.setdefaulttimeout(5)

from django import template
from django.conf import settings
from django.contrib.sites.models import get_current_site

from loci.utils import geocode, geolocate_request

from intellicast.utils import thirtysix_hour_outlook
from intellicast.tasks import prefetch_intellicast_data

"""
Summary of Template Tags and Syntax:

get_weather_conditions as [var_name]
get_weather_alerts as [var_name]

"""

register = template.Library()

class GetExtendedConditions(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name
        
    def render(self, context):
        try:
            request = context['request']
            zip_code = get_current_site(request).profile.zip_code
        except (KeyError, AttributeError):
            zip_code = settings.DEFAULT_ZIP_CODE
        try:
            (location, conditions, hourly_forecasts, daily_forecasts, alerts) = prefetch_intellicast_data(zip_code)
            (twelve_hour, twentyfour_hour, thirtysix_hour) = thirtysix_hour_outlook(daily_forecasts)
            if not conditions:
                return ''
            city_name = location['city'] + ',' + location['state']
            recent_precip = conditions['SixHrPrecip']
        except:
            if settings.DEBUG:
                raise
            return ''
            
        conditions_badge = {
            'city_name': city_name, 
            'zipcode': zip_code,
            'recent_precip': recent_precip,
            'current_temp': conditions['TempF'], 
            'icon_code': conditions['IconCode'],
            'feels_like': conditions['FeelsLikeF'],
            'wind_direction': conditions['WndDirCardinal'],
            'wind_speed': conditions['WndSpdMph'],
            'sky': conditions['Sky'],
            'twelve_hour': twelve_hour,
            'twentyfour_hour': twentyfour_hour,
            'thirtysix_hour': thirtysix_hour
        }
        context[self.var_name] = conditions_badge
        return ''
        
@register.tag
def get_extended_weather_conditions(parser, token):
    """
    Get the weather conditions for the current site's default zipcode.
    
    Syntax:
    {% get_current_conditions as [var_name] %}
    """
    
    args = token.split_contents()
    var_name = args[-1]
    return GetExtendedConditions(var_name)



class GetConditions(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name
        
    def render(self, context):
        try:
            request = context['request']
            zip_code = get_current_site(request).profile.zip_code
        except (KeyError, AttributeError):
            zip_code = settings.DEFAULT_ZIP_CODE
        try:
            (location, conditions, hourly_forecasts, daily_forecasts, alerts) = prefetch_intellicast_data(zip_code)
        
            conditions_badge = {
                'zipcode': zip_code, 
                'current_temp': conditions['TempF'], 
                'icon_code': conditions['IconCode'],
                'feels_like': conditions['FeelsLikeF'],
                'wind_direction': conditions['WndDirCardinal'],
                'wind_speed': conditions['WndSpdMph'],
                'sky': conditions['Sky'],
            }
            context[self.var_name] = conditions_badge
        except:
            return ''
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
            request = context['request']
            zip_code = get_current_site(request).profile.zip_code
        except (KeyError, AttributeError):
            zip_code = settings.DEFAULT_ZIP_CODE
        else:
            if not zip_code:
                zip_code = settings.DEFAULT_ZIP_CODE
        try:
            (location, conditions, hourly_forecasts, daily_forecasts, alerts) = prefetch_intellicast_data(zip_code)
        except TypeError:
            return ''
        except:
            #if settings.DEBUG:
            #    raise
            return ''
        try:
            alert_items = []
            for i, item in enumerate(alerts, 1):
                alerts_dict = alerts[i]                
                alert_item = {
                    'headline': alerts_dict['Headline'],
                    'starttime': alerts_dict['StartTime'],
                    'endtime': alerts_dict['EndTime'],
                    'urgency': alerts_dict['Urgency'],
                    'bulletin': string.lower(alerts_dict['Bulletin']),
                }
                alert_items.append(alert_item)
            context[self.var_name] = alert_items
        except:
            pass
        
        return ''
        
@register.tag
def get_weather_alerts(parser, token):
    """
    Get the weather alerts, if there are any, for the current site's default zipcode.
    
    Syntax:
    {% get_weather_alerts as [var_name] %}
    """
    
    args = token.split_contents()
    var_name = args[-1]
    return GetAlerts(var_name)

