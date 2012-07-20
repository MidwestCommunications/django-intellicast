# Create your views here.
import datetime
import time
import string

from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.contrib.sites.models import get_current_site
from django.utils import timezone

from loci.utils import geolocate_request, geocode
from loci.forms import GeolocationForm

from intellicast.utils import parse_intellicast_date, parse_intellicast_time
from intellicast.utils import thirtysix_hour_outlook
from intellicast.utils import get_intellicast_data, create_forecast_dict


def _get_request_location(request):
    location = geolocate_request(request)
    # need to make sure the location has a ZIP for intellicast
    if not location.zip_code:
        try:
            zip_code = get_current_site(request).profile.zip_code
        except AttributeError:
            zip_code = settings.DEFAULT_ZIP_CODE
        else:
            if not zip_code:
                zip_code = settings.DEFAULT_ZIP_CODE
        location = geocode(zip_code)
        location.zip_code = zip_code
    return location


def weather_page(request):
    """
    Main weather landing page.  Features current conditions, a 36 hour forecast,
    and an interactive map (sadly, map is flash.)
    """
    rloc = _get_request_location(request)
    geo_form = GeolocationForm(initial={'geo': rloc.zip_code})
    (location, conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(rloc.zip_code)

    if not hourly_forecasts or not conditions or not daily_forecasts:
        return render(request, 'intellicast/weather.html', {'unavailable': True})

    hourly_forecast_items = []
    for i in range(1, 24):
        forecast_dict = hourly_forecasts[str(i)]
        forecast_clean = create_forecast_dict('Hourly', forecast_dict)
        hourly_forecast_items.append(forecast_clean)
    
    daily_forecast_items = []
    for i in range(2, 9):
        forecast_dict = daily_forecasts[str(i)]
        forecast_clean = forecast_clean = create_forecast_dict('Daily', forecast_dict)
        daily_forecast_items.append(forecast_clean)
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
    except:
        pass
    
    (forecast_12hr, forecast_24hr, forecast_36hr) = thirtysix_hour_outlook(daily_forecasts)
    
    today = timezone.now().date()
    return render(request, 'intellicast/weather.html', {
        'location': location,
        'todays_date': today,
        'tomorrows_date': today + datetime.timedelta(days=1),
        'current_conditions': conditions,
        
        'forecast_12hr': forecast_12hr,
        'forecast_24hr': forecast_24hr,
        'forecast_36hr': forecast_36hr,

        'daily_forecasts': daily_forecast_items,
        'hourly_forecasts': hourly_forecast_items,
        'alerts': alert_items,
        'unavailable': False,
        'geo_form': geo_form,
    })

def daily_weather_detail(request, year=None, month=None, day=None):
    
    forecast_date = datetime.date(year=int(year), month=int(month), day=int(day))
    today = timezone.now().date()
    if forecast_date < today:
        return render(request, 'intellicast/daily_weather_detail.html', {'unavailable': True})
    
    difference = forecast_date - today
    day_index = str(1 + difference.days)
    
    try:
        rloc = _get_request_location(request)
        geo_form = GeolocationForm(initial={'geo': rloc.zip_code})
        (location, conditions, hourly_forecasts, daily_forecasts, alerts) = get_intellicast_data(rloc.zip_code)
    except TypeError:
        return render(request, 'intellicast/daily_weather_detail.html', {'unavailable': True})
    
    if int(day_index) > 1:
        prev_date = forecast_date - datetime.timedelta(days=1)
    else:
        prev_date = None
    
    if int(day_index) < 7:
        next_date = forecast_date + datetime.timedelta(days=1)
    else:
        next_date = None
   
    if not daily_forecasts:
        return render(request, 'intellicast/daily_weather_detail.html', {'unavailable': True})
    try:
        forecast = daily_forecasts[day_index]
    except KeyError:
        return render(request, 'intellicast/daily_weather_detail.html', {'unavailable': True})

    day_forecast_dict = create_forecast_dict('Day', forecast)
    night_forecast_dict = create_forecast_dict('Night', forecast)
    
    return render(request, 'intellicast/daily_weather_detail.html', {
        'location': location,
        'forecast_date': forecast_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'day_forecast': day_forecast_dict,
        'night_forecast': night_forecast_dict,
        'unavailable': False,
        'geo_form': geo_form,
    })  
