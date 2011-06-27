import datetime
from urllib import urlopen
from xml.dom.minidom import parse

from django.core.cache import cache
from django.conf import settings
from PIL import Image

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
            #Really hackity way to ensure we don't accidently get Pollen forecast here.
            try:
                mini_dict['PollenType']
            except KeyError:
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

def get_intellicast_location_old(zipcode):
    
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




def get_intellicast_location(zipcode):
    
    cname_location = 'intellicast_location_' + str(zipcode)
    cached_data_location = cache.get(cname_location)
    if cached_data_location:
        location = cached_data_location
    else:
        i_location = IntellicastLocation(zipcode)
        location = {
            'intellicast_id': i_location.location_id,
            'city': i_location.city,
            'state': i_location.state,
            'zipcode': zipcode,
            'latitude': i_location.lat,
            'longitude': i_location.lon
        }
        cache.set(cname_location, location, 60 * 60 * 24)
    return location
        


def get_intellicast_data(location):
    
    cname = 'intellicast_feed_data_' + str(location['zipcode'])
    cached_data = cache.get(cname)
    if cached_data:
        (conditions, hourly_forecasts, daily_forecasts, alerts) = cached_data
    else:
        feed = IntellicastFeed(location['intellicast_id'])
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
    
    if am_pm == 'PM' and hour != 12:
        hour = hour + 12
    if hour == 12 and am_pm == 'AM':
        hour = 0
            
    return datetime.datetime(year=year,month=month,day=day,hour=hour,minute=minute)
    
def fetch_intellicast_map_image():
    import urllib2
    from PIL import Image
    from django.conf import settings
    import os
    
    url = "http://services.intellicast.com/200904-01/158765827/Image/Radar/Radar2009.13L/SectorName/r03"
    #url = "http://services.intellicast.com/200904-01/158765827/Image/Radar/Radar2009.13L/Loop/SectorName/r03"
    req = urllib2.Request(url)
    f = urllib2.urlopen(req)
    try:
        local = open(settings.MEDIA_ROOT + 'intellicast/intellicast_map.gif', 'wb')
    except IOError:
        os.mkdir(settings.MEDIA_ROOT + 'intellicast/')
        local = open(settings.MEDIA_ROOT + 'intellicast/intellicast_map.gif', 'wb')
    
    local.write(f.read())
    local.close()
    
    im=Image.open(settings.MEDIA_ROOT + 'intellicast/intellicast_map.gif')
    return im
    
def get_cropped_intellicast_image(zipcode):
    """
    Zipcode/Market Mapping:
    54403 - Wausau
    55811 - Duluth
    54303 - Green Bay
    49001 - Kalamazoo
    48842 - Lansing
    49422 - Holland
    49017 - Battle Creek
    54914 - Appleton
    53085 - Sheboygan
    55747 - Hibbing
    49036 - Coldwater
    47802 - Terre Haute
    """
    
    zipcode = str(zipcode)
    
    cname = "intellicast_frontpage_maps"
    fp_map_url = cache.get(cname)
    if fp_map_url:
        return 'intellicast/intellicast_map_cropped_' + zipcode + '.gif'
    
    midwest_img = fetch_intellicast_map_image()
    
    wausau = midwest_img.crop( (160, 147, 290, 207) ).resize((130, 60))
    duluth = midwest_img.crop( (125, 91, 255, 151) ).resize((130, 60))
    green_bay = midwest_img.crop( (218, 161, 348, 221) ).resize((130, 60))
    terre_haute = midwest_img.crop( (225, 313, 355, 373 ) ).resize((130, 60))
    kalamazoo = midwest_img.crop( (275, 221, 405, 281) ).resize((130, 60))
    lansing = midwest_img.crop( (297, 203, 427, 263) ).resize((130, 60))
    holland = midwest_img.crop( (260, 206, 390, 266) ).resize((130, 60))
    battle_creek = midwest_img.crop( (284, 224, 284 + 130, 224 + 60) ).resize((130, 60))
    appleton = midwest_img.crop( (200, 168, 200 + 130, 168 + 60) ).resize((130, 60))
    sheboygan = midwest_img.crop( (218, 188, 218 + 130, 188 + 60) ).resize((130, 60))
    hibbing = midwest_img.crop( (98, 66, 98 + 130, 66 + 60) ).resize((130, 60))
    coldwater = midwest_img.crop( (284, 240, 284 + 130, 240 + 60) ).resize((130, 60))
    
    image_list = [(wausau, '54403'), (duluth, '55811'), (green_bay, '54303'),
                  (terre_haute, '47802'), (kalamazoo, '49001'),
                  (lansing, '48842'), (holland, '49422'), (battle_creek, '49017'),
                  (appleton, '54914'), (sheboygan, '53085'),
                  (hibbing, '55747'), (coldwater, '49036')]
    
    for image in image_list:
        image_file = image[0].save(
            settings.MEDIA_ROOT + 'intellicast/intellicast_map_cropped_' + 
            image[1] + '.gif')
        image_obj = Image.open(open(
            settings.MEDIA_ROOT + 'intellicast/intellicast_map_cropped_' + 
            image[1] + '.gif', 'rb'))
    
    cache.set(cname, 'data cached.', 60 * 15)
    return 'intellicast/intellicast_map_cropped_' + zipcode + '.gif'
    