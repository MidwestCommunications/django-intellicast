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
from intellicast.utils import get_intellicast_location, get_intellicast_data

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
        if parse_intellicast_date(forecast_dict['ValidDateLocal']).hour == 23:
            last_of_day = True
            print "got one"
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
    for i in range(2, 10):
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
    
    todays_forecast = daily_forecasts['1']
    if todays_forecast['IconCodeDay'] == '86':
        todays_forecast_dict = None
    else:
        todays_forecast_dict = {
            'shortname': 'Today',
            'temp': todays_forecast['HiTempF'],
            'temp-type': 'High',
            'precip_chance': todays_forecast['PrecipChanceDay'],
            'wind_speed': todays_forecast['WndSpdMph'],
            'wind_direction': todays_forecast['WndDirCardinal'],
            'sky': todays_forecast['SkyTextDay'],
            'icon_code': todays_forecast['IconCodeDay']
        }
    
    tonights_forecast_dict = {
        'shortname': 'Tonight',
        'temp': todays_forecast['LoTempF'],
        'temp-type': 'Low',
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
        'temp-type': 'High',
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
            'temp-type': 'Low',
            'precip_chance': tomorrows_forecast['PrecipChanceNight'],
            'wind_speed': tomorrows_forecast['WndSpdMph'],
            'wind_direction': tomorrows_forecast['WndDirCardinal'],
            'sky': tomorrows_forecast['SkyTextDay'],
            'icon_code': tomorrows_forecast['IconCodeDay']
        }
    
    print "today (daytime):", todays_forecast_dict
    print "tonight:", tonights_forecast_dict
    print "tomorrow: (daytime)", tomorrows_forecast_dict
    print "tomorrow night:", tomorrow_nights_forecast_dict
    
    if todays_forecast_dict:
        twelve_hr_forecast = todays_forecast_dict
        twentyfour_hr_forecast = tonights_forecast_dict
        thirtysix_hr_forecast = tomorrows_forecast_dict
    else:
        twelve_hr_forecast = tonights_forecast_dict
        twentyfour_hr_forecast = tomorrows_forecast_dict
        thirtysix_hr_forecast = tomorrow_nights_forecast_dict
    
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
        
        'forecast_12hr': twelve_hr_forecast,
        'forecast_24hr': twentyfour_hr_forecast,
        'forecast_36hr': thirtysix_hr_forecast,

        'daily_forecasts': daily_forecast_items,
        'hourly_forecasts': hourly_forecast_items,
        'alerts': alert_items,
        'unavailable': False
    }, context_instance = RequestContext(request))    

def daily_weather_detail(request, year=None, month=None, day=None):
    
    #today = datetime.datetime.now()
    #print 'today:', today 
    #day='4'
    #forecast_date = parse_intellicast_date('6/12/2011 6:54:00 PM')
    #print 'date:', forecast_date
    #print "difference:", forecast_date - today
    
    #forecast_date = datetime.datetime.now() + datetime.timedelta(days=int(day))
    
    
    forecast_date = datetime.date(year=int(year), month=int(month), day=int(day))
    difference = forecast_date - datetime.date.today()
    print "difference:", difference.days
    day = str(1 + difference.days)
    
    
    
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
        'uv_description': forecast['UvDescr'],
        'date_string': forecast['ValidDateLocal']
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
    
    if int(day) > 1:
        prev_date = forecast_date - datetime.timedelta(days=1)
    else:
        prev_date = None
    
    if int(day) < 7:
        next_date = forecast_date + datetime.timedelta(days=1)
    else:
        next_date = None
    
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
    
    
    
    
    
    
    
def parse_intellicast_date(date_as_string):    
    date_list = date_as_string.split(' ')
    date = date_list[0]
    time = date_list[1]
    am_pm = date_list[2]
    
    date_split = date.split('/')
    month=int(date_split[0])
    day=int(date_split[1])
    year=int(date_split[2])
    
    time_split = time.split(':')
    hour=int(time_split[0])
    minute=int(time_split[1])
    
    if am_pm == 'PM':
        hour = hour + 12
    
    if hour == 24:
        hour = 0
        #am_pm = 'AM'
    #hour = hour - 1
    
    print "hour", hour
    
    return datetime.datetime(year=year,month=month,day=day,hour=hour,minute=minute)


    