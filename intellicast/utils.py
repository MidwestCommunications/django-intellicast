import datetime
import requests

from urllib2 import urlopen
from xml.dom.minidom import parse, parseString

from django.core.cache import cache
from django.conf import settings
from django.contrib.sites.models import Site
from PIL import Image
from requests.exceptions import ConnectionError, HTTPError

DATA_MAPPING = {
    'HiTempF': 'temp',
    'LoTempF': 'temp',
    'TempF': 'temp',
    'PrecipChanceDay': 'precip_chance',
    'PrecipChanceNight': 'precip_chance',
    'PrecipChance': 'precip_chance',
    'WndSpdMph': 'wind_speed',
    'WndSpdMphNight': 'wind_speed',
    'WndDirCardinal': 'wind_direction',
    'WndDirCardinalNight': 'wind_direction',
    'SkyTextDay': 'sky',
    'SkyTextNight': 'sky',
    'SkyMedium': 'sky',
    'IconCode': 'icon_code',
    'IconCodeDay': 'icon_code',
    'IconCodeNight': 'icon_code',
    'RelHumidity': 'humidity',
    'RelHumidityNight': 'humidity',
    'Sunrise': 'sunrise',
    'UvIdx': 'uv_index',
    'UvDescr': 'uv_description',
    'ValidDateLocal': 'time_string',
    'Sunset': 'sunset',
    'MoonPhaseText': 'moon_phase',
    'HeatIdxF': 'temp',
    'ShortPhrase': 'phrase',
    'DayOfWk': 'weekday'
}

def process_intellicast_data(forecast_data):
    processed_data = {}
    for (intellicast_key, local_key) in DATA_MAPPING.items():
        try:
            data_item = forecast_data[intellicast_key]
        except KeyError:
            continue
        if data_item:
            processed_data[local_key] = data_item
    return processed_data

def _request_data(request_url):
    try:
        location_xml = parseString(requests.get(request_url).text)
        location_node = location_xml.getElementsByTagName('City')[0]
    except (IndexError, ConnectionError, HTTPError, AttributeError):
        return None
    return location_node

def create_forecast_dict(context, forecast_data):
    forecast_date = parse_intellicast_date(forecast_data['ValidDateLocal'])

    forecast_dict = process_intellicast_data(forecast_data)
    forecast_dict['datetime'] = forecast_date
    forecast_dict['shortname'] = context

    return forecast_dict

def get_intellicast_data(zipcode, long_cache=False, force=False):
    """
    Returns a set of intellicast data for the specified zipcode. In practice,
    this data should always be cached for our station's default zipcodes.
    """
    zipcode = str(zipcode)
    #Make sure we aren't accepting non-US zip codes
    if ' ' in zipcode or len(zipcode) < 5:
        return (None, None, None, None, None)

    cached_location = cache.get('intellicast_location_' + zipcode)

    if cached_location:
        location = cached_location
    else:
        location_node = _request_data('http://services.intellicast.com/' + 
            '200904-01/158765827/Locations/Cities/' + zipcode)
        if not location_node:
            return (None, None, None, None, None)

        location = {
            'intellicast_id': location_node.getAttribute('Id'),
            'city': location_node.getAttribute('Name'),
            'state': location_node.getAttribute('StateAbbr'),
            'zipcode': zipcode,
            'latitude': location_node.getAttribute('Latitude'),
            'longitude': location_node.getAttribute('Longitude'),
        }
        # Cache locations for 12 hours at a time per intellicast business rules.
        cache.set('intellicast_location_' + zipcode, location, 60 * 60 * 12)

    if not force:
        cached_intellicast_data = cache.get('intellicast_data_for_' + zipcode)
        if cached_intellicast_data:
            return cached_intellicast_data

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
        caching_duration = 60 * 60 * 24 #24 hours
    else:
        caching_duration = 60 * 60 * 4  #4 hours

    intellicast_data = (location, conditions_dict, hourly_forecast_dict, daily_forecast_dict, alerts_dict)

    cache.set('intellicast_data_for_' + zipcode,
        (intellicast_data), caching_duration)
    
    return intellicast_data

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
        todays_forecast_dict = create_forecast_dict('Today', todays_forecast)
    tonights_forecast_dict = create_forecast_dict('Tonight', todays_forecast)

    tomorrows_forecast = daily_forecasts['2']
    tomorrows_forecast_dict = create_forecast_dict('Tomorrow', tomorrows_forecast)
    
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
        tomorrow_nights_forecast_dict = create_forecast_dict(weekdays_dict[tomorrow] + ' Night', tomorrows_forecast)[1]
    
    if todays_forecast_dict:
        twelve_hr_forecast = todays_forecast_dict
        twentyfour_hr_forecast = tonights_forecast_dict
        thirtysix_hr_forecast = tomorrows_forecast_dict
    else:
        twelve_hr_forecast = tonights_forecast_dict
        twentyfour_hr_forecast = tomorrows_forecast_dict
        thirtysix_hr_forecast = tomorrow_nights_forecast_dict
    
    return twelve_hr_forecast, twentyfour_hr_forecast, thirtysix_hr_forecast
