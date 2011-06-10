import datetime
from urllib import urlopen
from xml.dom.minidom import parse

from django.core.cache import cache

from intellicast.models import WeatherLocation

class IntellicastLocation:
    
    def __init__(self, zipcode):
        
        self.zipcode = zipcode
        
        self.location_url = 'http://services.intellicast.com/200904-01/158765827/Locations/Cities/' + zipcode
        self.options = ['Id', 'Name', 'StateAbbr', 'StateName', 'Latitude', 'Longitude']
        
        infos = self.get_data()
        
        self.location_id = infos['Id']
        self.city = infos['Name']
        self.state = infos['StateAbbr']
        self.lat = infos['Latitude']
        self.lon = infos['Longitude']
            
    def get_data(self):
        
        try:
            xml = parse(urlopen(self.location_url))
        except:
            return "No Feed Found."
            
        options_dict = {}
        already_fetched = False
        for node in xml.getElementsByTagName('City'):
            if already_fetched:
                break
            
            attrs = node.attributes.keys()
            for attr in attrs:
                if attr in self.options:
                    value = node.getAttribute(attr)
                    options_dict[attr] = value        
            already_fetched = True
        return options_dict

class IntellicastFeed:
    
    def __init__(self, intellicast_id):
        self.location_id = intellicast_id
        self.conditions_url = 'http://services.intellicast.com/200904-01/158765827/Weather/Report/' + self.location_id
        self.options = ['ReportTime', 'TempF', 'IconCode', 'Sky', 
                        'ValidDateLocal', 'ValidDateUtc', 'RelHumidity', 
                        'WndSpdMph', 'WndDirDegr', 'WndDirCardinal']

    def get_data(self):
        
        try:
            xml = parse(urlopen(self.conditions_url))
        except:
            return "No Feed Found."
        
        conditions_dict = {}
        already_fetched = False
        for node in xml.getElementsByTagName('CurrentObservation'):
            if already_fetched:
                break
            
            attrs = node.attributes.keys()
            for attr in attrs:
                value = node.getAttribute(attr)
                conditions_dict[attr] = value
            already_fetched = True
        
        hourly_forecast_dict = {}
        for node in xml.getElementsByTagName('Hour'):
            mini_dict = {}
            attrs = node.attributes.keys()
            for attr in attrs:
                value = node.getAttribute(attr)
                mini_dict[attr] = value
            hourly_forecast_dict[mini_dict['HourNum']] = mini_dict
            
        daily_forecast_dict = {}
        for node in xml.getElementsByTagName('Day'):
            mini_dict = {}
            attrs = node.attributes.keys()
            for attr in attrs:
                value = node.getAttribute(attr)
                mini_dict[attr] = value
            daily_forecast_dict[mini_dict['DayNum']] = mini_dict
        
        alert_elements = xml.getElementsByTagName('Alert')
        alerts_dict = {}
        
        if alert_elements:
            for i, node in enumerate(xml.getElementsByTagName('Alert'), 1):
                mini_dict = {}
                attrs = node.attributes.keys()
                for attr in attrs:
                    value = node.getAttribute(attr)
                    mini_dict[attr] = value
                alerts_dict[i] = mini_dict
            
        return conditions_dict, hourly_forecast_dict, daily_forecast_dict, alerts_dict

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


class CurrentConditions:
    def __init__(self, current_temp, icon_code, zipcode):
        self.current_temp = current_temp
        self.icon_code = icon_code
        self.zipcode = zipcode

class DailyForecast:
    def __init__(self, weekday, high_temp, low_temp, phrase, icon_code):
        self.weekday = weekday
        self.high_temp = high_temp
        self.low_temp = low_temp
        self.phrase = phrase
        self.icon_code = icon_code
        
class HourlyForecast:
    def __init__(self, time_string, temp, icon_code, sky, precip_chance):
        self.time_string = time_string
        self.temp = temp
        self.icon_code = icon_code
        self.sky = sky
        self.precip_chance = precip_chance