import re
import datetime
import string
from string import capwords

from django import template
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.cache import cache
from django.db.models import F, Q
from django.shortcuts import get_object_or_404

from intellicast.models import WeatherLocation
from intellicast.utils import get_intellicast_location, get_intellicast_data

"""
Summary of Template Tags and Syntax:

get_weather_conditions as [var_name]
get_weather_alerts as [var_name]

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
        
        try:
            location = get_intellicast_location(zipcode)
            (conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(location)
            
            conditions_badge = {
                'zipcode': zipcode, 
                'current_temp': conditions['TempF'], 
                'icon_code' : conditions['IconCode']
            }
            context[self.var_name] = conditions_badge
        except:
            pass        
        
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
        
        try:
            location = get_intellicast_location(zipcode)
            (conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(location)
        except:
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
                    'bulletin': alerts_dict['Bulletin'],
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
    {% get_weather_conditions as [var_name] %}
    """
    
    args = token.split_contents()
    var_name = args[-1]
    return GetAlerts(var_name)
