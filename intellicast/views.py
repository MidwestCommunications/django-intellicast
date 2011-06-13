# Create your views here.
import datetime
from string import capwords

from django.conf import settings

from django.contrib.sites.models import Site
from django.core.cache import cache
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response, redirect

from intellicast.utils import get_intellicast_location, get_intellicast_data
from intellicast.utils import parse_intellicast_date

def weather_page(request):
    
    try:        
        zipcode = request.GET.get('zipcode', settings.DEFAULT_ZIP_CODE)
    except AttributeError:
        zipcode = None
    
    try:
        location = get_intellicast_location(zipcode)
        (conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(location)
    except:
        return render_to_response('intellicast/weather.html', {
            'unavailable': True
        }, context_instance = RequestContext(request))
    
    hourly_forecast_items = []
    for i in range(1, 24):
        forecast_dict = hourly_forecasts[str(i)]
        if parse_intellicast_date(forecast_dict['ValidDateLocal']).hour == 23:
            last_of_day = True
        else:
            last_of_day = False
        forecast_clean = {
            'time_string':forecast_dict['ValidDateLocal'],
            'datetime':parse_intellicast_date(forecast_dict['ValidDateLocal']),
            'temp':forecast_dict['HeatIdxF'],
            'icon_code':forecast_dict['IconCode'],
            'sky':forecast_dict['SkyMedium'],
            'precip_chance':forecast_dict['PrecipChance'],
            'humidity':forecast_dict['RelHumidity'],
            'wind_speed': forecast_dict['WndSpdMph'],
            'wind_direction': forecast_dict['WndDirCardinal'],
            'lastofday': last_of_day
        }
        
        hourly_forecast_items.append(forecast_clean)
    
    daily_forecast_items = []
    for i in range(2, 9):
        forecast_dict = daily_forecasts[str(i)]
        forecast_clean = {
            'weekday':forecast_dict['DayOfWk'],
            'time_string':forecast_dict['ValidDateLocal'],
            'datetime':parse_intellicast_date(forecast_dict['ValidDateLocal']),
            'high_temp':forecast_dict['HiTempF'],
            'low_temp':forecast_dict['LoTempF'],
            'phrase':forecast_dict['ShortPhrase'],
            'icon_code':forecast_dict['IconCode'],
            'precip_chance':forecast_dict['PrecipChance'],
            'humidity':forecast_dict['RelHumidity'],
            'wind_speed': forecast_dict['WndSpdMph'],
            'wind_direction': forecast_dict['WndDirCardinal'],
        }
        
        daily_forecast_items.append(forecast_clean)
    
    (forecast_12hr, forecast_24hr, forecast_36hr) = thirtysix_hour_outlook(daily_forecasts)

    
    todays_date = datetime.datetime.now()
    tomorrows_date = datetime.datetime.now() + datetime.timedelta(days=1)
    
    template_name = "intellicast/weather.html"
    
    return render_to_response(template_name, {
        'location': location,
        'todays_date': todays_date,
        'tomorrows_date': tomorrows_date,
        'current_conditions': conditions,
        
        'forecast_12hr': forecast_12hr,
        'forecast_24hr': forecast_24hr,
        'forecast_36hr': forecast_36hr,

        'daily_forecasts': daily_forecast_items,
        'hourly_forecasts': hourly_forecast_items,
        'unavailable': False
    }, context_instance = RequestContext(request))    

def daily_weather_detail(request, year=None, month=None, day=None):
    
    forecast_date = datetime.date(year=int(year), month=int(month), day=int(day))
    difference = forecast_date - datetime.date.today()
    day_index = str(1 + difference.days)
    
    try:        
        zipcode = request.GET.get('zipcode', settings.DEFAULT_ZIP_CODE)
    except AttributeError:
        zipcode = None
    
    location = get_intellicast_location(zipcode)
    (conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(location)
    
    if int(day_index) > 1:
        prev_date = forecast_date - datetime.timedelta(days=1)
    else:
        prev_date = None
    
    if int(day_index) < 7:
        next_date = forecast_date + datetime.timedelta(days=1)
    else:
        next_date = None
    
    forecast = daily_forecasts[day_index]
    day_forecast_dict = {
        'high_temp': forecast['HiTempF'],
        'precip_chance': forecast['PrecipChanceDay'],
        'wind_speed': forecast['WndSpdMph'],
        'wind_direction': forecast['WndDirCardinal'],
        'sky': forecast['SkyTextDay'],
        'icon_code': forecast['IconCodeDay'],
        'humidity': forecast['RelHumidity'],
        'sunrise': forecast['Sunrise'],
        'uv_index': forecast['UvIdx'],
        'uv_description': forecast['UvDescr'],
        'date_string': forecast['ValidDateLocal'],
        'datetime': parse_intellicast_date(forecast['ValidDateLocal'])
    }
    night_forecast_dict = {
        'low_temp': forecast['LoTempF'],
        'precip_chance': forecast['PrecipChanceNight'],
        'wind_speed': forecast['WndSpdMphNight'],
        'wind_direction': forecast['WndDirCardinalNight'],
        'sky': forecast['SkyTextNight'],
        'icon_code': forecast['IconCodeNight'],
        'humidity': forecast['RelHumidityNight'],
        'sunset': forecast['Sunset'],
        'moon_phase': forecast['MoonPhaseText'],
        'datetime': parse_intellicast_date(forecast['ValidDateLocal'])
    }
    
    template_name = 'intellicast/daily_weather_detail.html'
    
    return render_to_response(template_name, {
        'location': location,
        'forecast_date': forecast_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'day_forecast': day_forecast_dict,
        'night_forecast': night_forecast_dict,
        'unavailable': False
    }, context_instance = RequestContext(request))  
    
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
    
    
    



    