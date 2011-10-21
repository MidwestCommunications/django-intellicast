# Create your views here.
import datetime
import time

from django.conf import settings
from django.shortcuts import get_object_or_404, render

from intellicast.utils import parse_intellicast_date, parse_intellicast_time
from intellicast.utils import get_intellicast_data, thirtysix_hour_outlook

def weather_page(request):
    """
    Main weather landing page.  Features current conditions, a 36 hour forecast,
    and an interactive map (sadly, map is flash.)
    """
    
    try:
        zipcode = request.GET.get('zipcode', settings.DEFAULT_ZIP_CODE)
        (location, conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(str(int(zipcode)))
    except (ValueError, IndexError):
        return render(request, 'intellicast/weather.html', {'unavailable': True})
    
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
    
    return render(request, 'intellicast/weather.html', {
        'location': location,
        'todays_date': datetime.datetime.now(),
        'tomorrows_date': datetime.datetime.now() + datetime.timedelta(days=1),
        'current_conditions': conditions,
        
        'forecast_12hr': forecast_12hr,
        'forecast_24hr': forecast_24hr,
        'forecast_36hr': forecast_36hr,

        'daily_forecasts': daily_forecast_items,
        'hourly_forecasts': hourly_forecast_items,
        'unavailable': False
    })

def daily_weather_detail(request, year=None, month=None, day=None):
    
    forecast_date = datetime.date(year=int(year), month=int(month), day=int(day))
    if forecast_date < datetime.date.today():
        template_name = 'intellicast/daily_weather_detail.html'
        return render(request, 'intellicast/daily_weather_detail.html', {
            'unavailable': True
        })
    
    difference = forecast_date - datetime.date.today()
    day_index = str(1 + difference.days)
    
    try:
        zipcode = request.GET.get('zipcode', settings.DEFAULT_ZIP_CODE)
        (location, conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(str(int(zipcode)))
    except (ValueError, IndexError):
        return render(request, 'intellicast/daily_weather_detail.html', {'unavailable': True})
    
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
        'sunrise': parse_intellicast_time(forecast['Sunrise']),
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
        'sunset': parse_intellicast_time(forecast['Sunset']),
        'moon_phase': forecast['MoonPhaseText'],
        'datetime': parse_intellicast_date(forecast['ValidDateLocal'])
    }
    
    return render(request, 'intellicast/daily_weather_detail.html', {
        'location': location,
        'forecast_date': forecast_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'day_forecast': day_forecast_dict,
        'night_forecast': night_forecast_dict,
        'unavailable': False
    })  
    

    
    
    



    
