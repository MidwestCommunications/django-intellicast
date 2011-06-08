# Create your views here.
import datetime
from string import capwords

from django.conf import settings

from django.contrib.sites.models import Site
from django.core.cache import cache
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response, redirect

from intellicast.models import WeatherLocation
from intellicast.utils import IntellicastLocation, IntellicastFeed
from intellicast.utils import DailyForecast, HourlyForecast

def weather_page(request):
    
    if request.GET.get('zipcode', 'none') != 'none':
        zipcode = str(request.GET.get('zipcode'))
    else:
        try:
            zipcode = settings.DEFAULT_ZIP_CODE
        except AttributeError:
            zipcode = None
    
    location = get_intellicast_location(zipcode)
    (conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(location)
    
    hourly_forecast_items = []
    for i in range(1, 24):
        forecast_dict = hourly_forecasts[str(i)]
        forecast_obj = HourlyForecast(
            time_string=forecast_dict['ValidDateLocal'],
            temp=forecast_dict['HeatIdxF'],
            icon_code=forecast_dict['IconCode'],
            sky=forecast_dict['SkyMedium'],
            precip_chance=forecast_dict['PrecipChance']
        )
        
        hourly_forecast_items.append(forecast_obj)
    
    daily_forecast_items = []
    for i in range(2, 10):
        forecast_dict = daily_forecasts[str(i)]
        forecast_obj = DailyForecast(
            weekday=forecast_dict['DayOfWk'],
            high_temp=forecast_dict['HiTempF'],
            low_temp=forecast_dict['LoTempF'],
            phrase=forecast_dict['ShortPhrase'],
            icon_code=forecast_dict['IconCode']
        )
        
        daily_forecast_items.append(forecast_obj)
    
    todays_forecast = daily_forecasts['1']
    todays_forecast_dict = {
        'high_temp': todays_forecast['HiTempF'],
        'precip_chance': todays_forecast['PrecipChanceDay'],
        'wind_speed': todays_forecast['WndSpdMph'],
        'wind_direction': todays_forecast['WndDirCardinal'],
        'sky': todays_forecast['SkyTextDay'],
        'icon_code': todays_forecast['IconCodeDay']
    }
    
    tonights_forecast_dict = {
        'low_temp': todays_forecast['LoTempF'],
        'precip_chance': todays_forecast['PrecipChanceNight'],
        'wind_speed': todays_forecast['WndSpdMphNight'],
        'wind_direction': todays_forecast['WndDirCardinalNight'],
        'sky': todays_forecast['SkyTextNight'],
        'icon_code': todays_forecast['IconCodeNight']
    }
    
    tomorrows_forecast = daily_forecasts['2']
    tomorrows_forecast_dict = {
        'high_temp': todays_forecast['HiTempF'],
        'precip_chance': todays_forecast['PrecipChance'],
        'wind_speed': todays_forecast['WndSpdMph'],
        'wind_direction': todays_forecast['WndDirCardinal'],
        'sky': todays_forecast['SkyText'],
        'icon_code': todays_forecast['IconCode']
    }
    
    print "today:", todays_forecast_dict
    print "tonight:", tonights_forecast_dict
    print "tomorrow:", tomorrows_forecast_dict
    
    alert_items = []
    for i, item in enumerate(alerts, 1):
        alerts_dict = alerts[i]
        
        bulletin = alerts_dict['Bulletin']
        #bulletin_split = bulletin.split('/', 2)
        
        alerts_obj = (alerts_dict['Headline'], alerts_dict['Bulletin'], alerts_dict['StartTime'], alerts_dict['EndTime'])
        
        alert_items.append(alerts_obj)
    
    
    template_name = "intellicast/weather.html"
    
    return render_to_response(template_name, {
        'location': location,
        
        'current_conditions': conditions,
        'todays_forecast': todays_forecast_dict,
        'tonights_forecast': tonights_forecast_dict,
        'tomorrows_forecast': tomorrows_forecast_dict,

        'daily_forecasts': daily_forecast_items,
        'hourly_forecasts': hourly_forecast_items,
        'alerts': alert_items,
        'unavailable': False
    }, context_instance = RequestContext(request))    

def daily_weather_detail(request):
    
    day='4'
    
    forecast_date = datetime.datetime.now() + datetime.timedelta(days=int(day))
    
    if request.GET.get('zipcode', 'none') != 'none':
        zipcode = str(request.GET.get('zipcode'))
    else:
        try:
            zipcode = settings.DEFAULT_ZIP_CODE
        except AttributeError:
            zipcode = None
    
    location = get_intellicast_location(zipcode)
    (conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(location)
    
    forecast = daily_forecasts[day]
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
        'uv_description': forecast['UvDescr']
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
        'moon_phase': forecast['MoonPhaseText']
    }
    
    template_name = 'intellicast/daily_weather_detail.html'
    
    return render_to_response(template_name, {
        'location': location,
        'forecast_date': forecast_date,
        'day_forecast': day_forecast_dict,
        'night_forecast': night_forecast_dict,
        'unavailable': False
    }, context_instance = RequestContext(request))  
    
    
    
    
    
    
    
    
    
    
    

def get_intellicast_location(zipcode):
    
    cname_location = 'intellicast_location_' + str(zipcode)
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
                return render_to_response('intellicast/weather.html', {
                    'unavailable': True,
                }, context_instance = RequestContext(request))
                
                
            location = WeatherLocation.objects.create(
                intellicast_id=i_location.location_id,
                city=i_location.city,
                state=i_location.state,
                zipcode=zipcode,
                latitude=i_location.lat,
                longitude=i_location.lon
            )
        cache.set(cname_location, location, 60 * 60 * 24)
    return location
    
def get_intellicast_data(location):
    
    cname = 'intellicast_feed_data_' + str(location.zipcode)
    cached_data = cache.get(cname)
    if cached_data:
        (conditions, hourly_forecasts, daily_forecasts, alerts) = cached_data
    else:
        feed = IntellicastFeed(location.intellicast_id)
        conditions, hourly_forecasts, daily_forecasts, alerts = feed.get_data()
        cache.set(cname, (conditions, hourly_forecasts, daily_forecasts, alerts), 1200)
        
    return conditions, hourly_forecasts, daily_forecasts, alerts
    