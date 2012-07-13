import datetime
import requests

from urllib2 import urlopen
from xml.dom.minidom import parse, parseString

from django.core.cache import cache
from django.conf import settings
from django.contrib.sites.models import Site
from PIL import Image
from requests.exceptions import ConnectionError, HTTPError

def _request_data(request_url):
    try:
        location_xml = parseString(requests.get(request_url).text)
    except (ConnectionError, HTTPError, AttributeError):
        return None, None, None, None, None
    try:
        location_node = location_xml.getElementsByTagName('City')[0]
        return location_node
    except IndexError, AttributeError:
        return None, None, None, None, None

def _create_forecast_dict(context, forecast_data):
    forecast_dict_day = {
        'shortname': context,
        'temp': forecast_data['HiTempF'],
        'temp_type': 'High',
        'precip_chance': forecast_data['PrecipChanceDay'],
        'wind_speed': forecast_data['WndSpdMph'],
        'wind_direction': forecast_data['WndDirCardinal'],
        'sky': forecast_data['SkyTextDay'],
        'icon_code': forecast_data['IconCodeDay']
    }

    forecast_dict_night = {
        'shortname': context,
        'temp': forecast_data['LoTempF'],
        'temp_type': 'Low',
        'precip_chance': forecast_data['PrecipChanceNight'],
        'wind_speed': forecast_data['WndSpdMphNight'],
        'wind_direction': forecast_data['WndDirCardinalNight'],
        'sky': forecast_data['SkyTextNight'],
        'icon_code': forecast_data['IconCodeNight']
    }

    return (forecast_dict_day, forecast_dict_night)

def get_intellicast_data(zipcode, long_cache=False):
    """
    Returns a set of intellicast data for the specified zipcode. In practice,
    this data should always be cached for our station's default zipcodes.
    """
    cached_location = cache.get('intellicast_location_' + zipcode)
    if cached_location:
        location = cached_location
    else:
        location_node = _request_data('http://services.intellicast.com/' + 
            '200904-01/158765827/Locations/Cities/' + zipcode)

        try:
            location = {
                'intellicast_id': location_node.getAttribute('Id'),
                'city': location_node.getAttribute('Name'),
                'state': location_node.getAttribute('StateAbbr'),
                'zipcode': zipcode,
                'latitude': location_node.getAttribute('Latitude'),
                'longitude': location_node.getAttribute('Longitude'),
            }
        except AttributeError:
            return None, None, None, None, None
        # Cache locations for 12 hours at a time per intellicast business rules.
        cache.set('intellicast_location_' + str(zipcode), location, 60 * 60 * 12)

    xml_data=_request_data('http://services.intellicast.com/200904-01/' + 
        '158765827/Weather/Report/' + location['intellicast_id'])

    conditions_dict = {}
    conditions_node = xml_data.getElementsByTagName('CurrentObservation')[0]
    for attr in conditions_node.attributes.keys():
        conditions_dict[attr] = conditions_node.getAttribute(attr)
    
    hourly_forecast_dict = {}
    for node in xml_data.getElementsByTagName('Hour'):
        mini_dict = {}
        for attr in node.attributes.keys():
            mini_dict[attr] = node.getAttribute(attr)
        hourly_forecast_dict[mini_dict['HourNum']] = mini_dict
    
    daily_forecast_dict = {}
    daily_forecast_node = xml_data.getElementsByTagName('DailyForecast')[0]
    for node in daily_forecast_node.getElementsByTagName('Day'):
        mini_dict = {}
        for attr in node.attributes.keys():
            mini_dict[attr] =  node.getAttribute(attr)
        daily_forecast_dict[mini_dict['DayNum']] = mini_dict
    
    alerts_dict = {}
    alert_elements = xml_data.getElementsByTagName('Alert')
    if alert_elements:
        for i, node in enumerate(alert_elements, 1):
            mini_dict = {}
            for attr in node.attributes.keys():
                mini_dict[attr] = node.getAttribute(attr)
            alerts_dict[i] = mini_dict

    #This is allowed to cache data for development
    if long_cache:
        caching_duration = 60 * 60 * 24
    else:
        caching_duration = 60 * 60 * 4

    cache.set('intellicast_data_for_' + str(zipcode), 
        (location, conditions_dict, hourly_forecast_dict, daily_forecast_dict, alerts_dict), caching_duration)
    if zipcode:
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
        todays_forecast_dict = _create_forecast_dict('Today', todays_forecast)[0]
    tonights_forecast_dict = _create_forecast_dict('Tonight', todays_forecast)[1]

    tomorrows_forecast = daily_forecasts['2']
    tomorrows_forecast_dict = _create_forecast_dict('Tomorrow', tomorrows_forecast)[0]
    
    if todays_forecast_dict:
        tomorrow_nights_forecast_dict = None
    else:
        weekdays_dict = {
            0: 'Mon',
            1: 'Tues',
            2: 'Wed',
            3: 'Thurs',
            4: 'Fri',
            5: 'Sat',
            6: 'Sun'
        }

        tomorrow = datetime.date.today().weekday() + 1
        tomorrow_nights_forecast_dict = _create_forecast_dict(weekdays_dict[tomorrow] + ' Night', tomorrows_forecast)[1]
    
    if todays_forecast_dict:
        twelve_hr_forecast = todays_forecast_dict
        twentyfour_hr_forecast = tonights_forecast_dict
        thirtysix_hr_forecast = tomorrows_forecast_dict
    else:
        twelve_hr_forecast = tonights_forecast_dict
        twentyfour_hr_forecast = tomorrows_forecast_dict
        thirtysix_hr_forecast = tomorrow_nights_forecast_dict
    
    return twelve_hr_forecast, twentyfour_hr_forecast, thirtysix_hr_forecast
