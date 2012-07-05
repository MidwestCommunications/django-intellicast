import datetime
import requests

from urllib2 import urlopen
from xml.dom.minidom import parse, parseString

from django.core.cache import cache
from django.conf import settings
from django.contrib.sites.models import Site
from PIL import Image


def get_intellicast_data(for_zip=None, long_cache=None):
    """
    Returns a set of intellicast data for the specified zipcode. In practice,
    this data should always be cached for our station's default zipcodes.
    """
    zipcode = for_zip
    cached_location = cache.get('intellicast_location_' + zipcode)
    if cached_location:
        location = cached_location
    else:
        location_xml = parseString(requests.get('http://services.intellicast.com/' + 
            '200904-01/158765827/Locations/Cities/' + zipcode).text)
                
        location_node = location_xml.getElementsByTagName('City')[0]
        location = {
            'intellicast_id': location_node.getAttribute('Id'),
            'city': location_node.getAttribute('Name'),
            'state': location_node.getAttribute('StateAbbr'),
            'zipcode': zipcode,
            'latitude': location_node.getAttribute('Latitude'),
            'longitude': location_node.getAttribute('Longitude'),
        }
        # Cache locations for 12 hours at a time per intellicast business rules.
        cache.set('intellicast_location_' + str(zipcode), location, 60 * 60 * 12)
    
    xml=parseString(requests.get('http://services.intellicast.com/200904-01/' + 
        '158765827/Weather/Report/' + location['intellicast_id']).text)

    conditions_dict = {}
    conditions_node = xml.getElementsByTagName('CurrentObservation')[0]
    for attr in conditions_node.attributes.keys():
        conditions_dict[attr] = conditions_node.getAttribute(attr)
    
    hourly_forecast_dict = {}
    for node in xml.getElementsByTagName('Hour'):
        mini_dict = {}
        for attr in node.attributes.keys():
            mini_dict[attr] = node.getAttribute(attr)
        hourly_forecast_dict[mini_dict['HourNum']] = mini_dict
    
    daily_forecast_dict = {}
    daily_forecast_node = xml.getElementsByTagName('DailyForecast')[0]
    for node in daily_forecast_node.getElementsByTagName('Day'):
        mini_dict = {}
        for attr in node.attributes.keys():
            mini_dict[attr] =  node.getAttribute(attr)
        daily_forecast_dict[mini_dict['DayNum']] = mini_dict
    
    alerts_dict = {}
    alert_elements = xml.getElementsByTagName('Alert')
    if alert_elements:
        for i, node in enumerate(alert_elements, 1):
            mini_dict = {}
            for attr in node.attributes.keys():
                mini_dict[attr] = node.getAttribute(attr)
            alerts_dict[i] = mini_dict
    caching_duration = 60 * 6
    #This is allowed to cache data for development
    if long_cache:
        caching_duration = 60 * 60 * 24

    if not long_cache and not for_zip:
        caching_duration = 60 * 60 * 4

    cache.set('intellicast_data_for_' + str(zipcode), 
        (location, conditions_dict, hourly_forecast_dict, daily_forecast_dict, alerts_dict), caching_duration)
    if for_zip:
        return location, conditions_dict, hourly_forecast_dict, daily_forecast_dict, alerts_dict

def parse_intellicast_date(date_as_string):    
    return datetime.datetime.strptime(date_as_string, '%m/%d/%Y %I:%M:%S %p')
    
def parse_intellicast_time(time_as_string):    
    return datetime.datetime.strptime(time_as_string, '%I:%M:%S %p').time

def thirtysix_hour_outlook(daily_forecasts):
    """
    Returns dictionaries for a 36 hour extended forecast as seen on mwc
    weather sites.
    """
    if not daily_forecasts:
        return None, None, None

    todays_forecast = daily_forecasts['1']
    if todays_forecast['IconCodeDay'] == '86':
        todays_forecast_dict = None
    else:
        todays_forecast_dict = {
            'shortname': 'Today',
            'temp': todays_forecast['HiTempF'],
            'temp_type': 'High',
            'precip_chance': todays_forecast['PrecipChanceDay'],
            'wind_speed': todays_forecast['WndSpdMph'],
            'wind_direction': todays_forecast['WndDirCardinal'],
            'sky': todays_forecast['SkyTextDay'],
            'icon_code': todays_forecast['IconCodeDay']
        }
    
    tonights_forecast_dict = {
        'shortname': 'Tonight',
        'temp': todays_forecast['LoTempF'],
        'temp_type': 'Low',
        'precip_chance': todays_forecast['PrecipChanceNight'],
        'wind_speed': todays_forecast['WndSpdMphNight'],
        'wind_direction': todays_forecast['WndDirCardinalNight'],
        'sky': todays_forecast['SkyTextNight'],
        'icon_code': todays_forecast['IconCodeNight']
    }
    
    tomorrows_forecast = daily_forecasts['2']
    tomorrows_forecast_dict = {
        'shortname': 'Tomorrow',
        'temp': tomorrows_forecast['HiTempF'],
        'temp_type': 'High',
        'precip_chance': tomorrows_forecast['PrecipChanceDay'],
        'wind_speed': tomorrows_forecast['WndSpdMph'],
        'wind_direction': tomorrows_forecast['WndDirCardinal'],
        'sky': tomorrows_forecast['SkyTextDay'],
        'icon_code': tomorrows_forecast['IconCodeDay']
    }
    
    if todays_forecast_dict:
        tomorrow_nights_forecast_dict = None
    else:
        weekdays_dict = {
            1: 'Sun',
            2: 'Mon',
            3: 'Tues',
            4: 'Wed',
            5: 'Thurs',
            6: 'Fri',
            7: 'Sat'
        }

        tomorrow_nights_forecast_dict = {
            'shortname': weekdays_dict[datetime.datetime.today().day] + ' Night',
            'temp': tomorrows_forecast['LoTempF'],
            'temp_type': 'Low',
            'precip_chance': tomorrows_forecast['PrecipChanceNight'],
            'wind_speed': tomorrows_forecast['WndSpdMph'],
            'wind_direction': tomorrows_forecast['WndDirCardinal'],
            'sky': tomorrows_forecast['SkyTextNight'],
            'icon_code': tomorrows_forecast['IconCodeDay']
        }
    
    if todays_forecast_dict:
        twelve_hr_forecast = todays_forecast_dict
        twentyfour_hr_forecast = tonights_forecast_dict
        thirtysix_hr_forecast = tomorrows_forecast_dict
    else:
        twelve_hr_forecast = tonights_forecast_dict
        twentyfour_hr_forecast = tomorrows_forecast_dict
        thirtysix_hr_forecast = tomorrow_nights_forecast_dict
    
    return twelve_hr_forecast, twentyfour_hr_forecast, thirtysix_hr_forecast
