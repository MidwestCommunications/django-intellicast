import datetime
#from time import strptime
#from time import mktime
import time

from urllib2 import urlopen
from xml.dom.minidom import parse

from django.core.cache import cache
from django.conf import settings
from PIL import Image

from intellicast.tasks import fetch_intellicast_data

def get_intellicast_data(zipcode):
    """
    Returns a set of intellicast data for the specified zipcode. In practice,
    this data should always be cached for our station's default zipcodes.
    """
    cname = 'intellicast_data_for_' + str(zipcode)
    cached_data = cache.get(cname)
    if cached_data:
        return cached_data
    else:
        return fetch_intellicast_data(zipcode)

def parse_intellicast_date(date_as_string):    
    return datetime.datetime.strptime(date_as_string, '%m/%d/%Y %I:%M:%S %p')
    
def parse_intellicast_time(time_as_string):    
    return datetime.datetime.fromtimestamp(time.mktime(time.strptime(time_as_string, '%I:%M:%S %p'))).time

def thirtysix_hour_outlook(daily_forecasts):
    """
    Returns dictionaries for a 36 hour extended forecast as seen on mwc
    weather sites.
    """
    
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
        tomorrow_nights_forecast_dict = {
            'shortname': 'Tomorrow Night',
            'temp': tomorrows_forecast['LoTempF'],
            'temp_type': 'Low',
            'precip_chance': tomorrows_forecast['PrecipChanceNight'],
            'wind_speed': tomorrows_forecast['WndSpdMph'],
            'wind_direction': tomorrows_forecast['WndDirCardinal'],
            'sky': tomorrows_forecast['SkyTextDay'],
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