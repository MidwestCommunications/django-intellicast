import os
import urllib2
from PIL import Image
from celery.decorators import task
from django.conf import settings
from django.core.cache import cache
from images2gif import writeGif

from urllib2 import urlopen, HTTPError
import requests
from xml.dom.minidom import parse, parseString
from django.contrib.sites.models import Site

@task(name='intellicast.fetch_intellicast_data')
def fetch_intellicast_data(for_zip=None):
    
    site_zip_codes=Site.objects.values_list('profile__zip_code', flat=True)

    if not for_zip:
        zipcodes_list = site_zip_codes
    else:
        # If a location which is a default site zipcode is being looked up,
        # only look in the cache to grab it so that this lookup is never
        # done at request time unless it's for an unusual location.
        if for_zip in site_zip_codes:
            cached_for_site = cache.get('intellicast_data_for_' + for_zip)
            if cached_for_site:
                return cached_for_site
            else:
                return None, None, None, None, None
        zipcodes_list = [for_zip]

    for zipcode in zipcodes_list:
        if zipcode == '':
            continue
        cached_location = cache.get('intellicast_location_' + zipcode)
        if cached_location:
            location = cached_location
        else:            
            location_xml = parseString(requests.get('http://services.intellicast.com/' + 
                '200904-01/158765827/Locations/Cities/' + zipcode).text)
                    
            location_node = location_xml.getElementsByTagName('City')[0]
            location = {
                'intellicast_id': location_node.getAttribute('Id'),
                'city': location_node.getAttribute('Name'),
                'state': location_node.getAttribute('StateAbbr'),
                'zipcode': zipcode,
                'latitude': location_node.getAttribute('Latitude'),
                'longitude': location_node.getAttribute('Longitude'),
            }
            # Cache locations for 12 hours at a time per intellicast business rules.
            cache.set('intellicast_location_' + str(zipcode), location, 60 * 60 * 12)
        
        xml=parseString(requests.get('http://services.intellicast.com/200904-01/' + 
            '158765827/Weather/Report/' + location['intellicast_id']).text)

        conditions_dict = {}
        conditions_node = xml.getElementsByTagName('CurrentObservation')[0]
        for attr in conditions_node.attributes.keys():
            conditions_dict[attr] = conditions_node.getAttribute(attr)
                
        hourly_forecast_dict = {}
        for node in xml.getElementsByTagName('Hour'):
            mini_dict = {}
            for attr in node.attributes.keys():
                mini_dict[attr] = node.getAttribute(attr)
            hourly_forecast_dict[mini_dict['HourNum']] = mini_dict
        
        daily_forecast_dict = {}
        daily_forecast_node = xml.getElementsByTagName('DailyForecast')[0]
        for node in daily_forecast_node.getElementsByTagName('Day'):
            mini_dict = {}
            for attr in node.attributes.keys():
                mini_dict[attr] =  node.getAttribute(attr)
            daily_forecast_dict[mini_dict['DayNum']] = mini_dict
        
        alerts_dict = {}
        alert_elements = xml.getElementsByTagName('Alert')
        if alert_elements:
            for i, node in enumerate(alert_elements, 1):
                mini_dict = {}
                for attr in node.attributes.keys():
                    mini_dict[attr] = node.getAttribute(attr)
                alerts_dict[i] = mini_dict
        cache.set('intellicast_data_for_' + str(zipcode), 
            (location, conditions_dict, hourly_forecast_dict, daily_forecast_dict, alerts_dict), 60 * 6)
        if for_zip:
            return location, conditions_dict, hourly_forecast_dict, daily_forecast_dict, alerts_dict



@task(name='intellicast.update_map_images')
def update_map_images():
    #Fetch a radar image of the Midwest from Intellicast and save it to disk.
    f = urllib2.urlopen(urllib2.Request(
        "http://services.intellicast.com/200904-01/158765827/Image/Radar/Radar2009.13L/Loop/SectorName/r03"
    ))
    try:
        local = open(settings.MEDIA_ROOT + 'intellicast/intellicast_animated_map.gif', 'wb')
    except IOError:
        os.mkdir(settings.MEDIA_ROOT + 'intellicast/')
        local = open(settings.MEDIA_ROOT + 'intellicast/intellicast_animated_map.gif', 'wb')    
    local.write(f.read())
    local.close()
    
    #Load up the fetched file from the disk
    original_file = Image.open(settings.MEDIA_ROOT + 'intellicast/intellicast_animated_map.gif')
    original_file.load()
    
    #Set up zipcodes with a list for their image frames
    frame = 0
    frames_dict = {
        '54403': [], '55811': [], '54303': [], '47802': [], 
        '49001': [], '48842': [], '49422': [], '49017': [],
        '54915': [], '53085': [], '55747': [], '49036': [], 
        'wisconsin': [], 'michigan_lower': [], 'michigan_upper': [],
        'minnesota': [], 'terre_haute': []
    }
    
    #Loop through the frames of the original images, cropping out frames for each region
    while True:
        try:
            original_file.seek(frame)
            
            frames_dict['54403'].append(original_file.copy().crop((160,147,290,207)).resize((130,60)))
            frames_dict['55811'].append(original_file.copy().crop((125,91,255,151)).resize((130,60)))
            frames_dict['54303'].append(original_file.copy().crop((218,161,348,221)).resize((130,60)))
            frames_dict['47802'].append(original_file.copy().crop((225,313,355,373)).resize((130,60)))
            frames_dict['49001'].append(original_file.copy().crop((275,221,405,281)).resize((130,60)))
            frames_dict['48842'].append(original_file.copy().crop((297,203,427,263)).resize((130,60)))
            frames_dict['49422'].append(original_file.copy().crop((260,206,390,266)).resize((130,60)))
            frames_dict['49017'].append(original_file.copy().crop((284,224,414,284)).resize((130,60)))
            frames_dict['54915'].append(original_file.copy().crop((200,168,330,228)).resize((130,60)))
            frames_dict['53085'].append(original_file.copy().crop((218,188,348,248)).resize((130,60)))
            frames_dict['55747'].append(original_file.copy().crop((98,66,228,126)).resize((130,60)))
            frames_dict['49036'].append(original_file.copy().crop((284,240,414,300)).resize((130,60)))
            
            frames_dict['wisconsin'].append(original_file.copy().crop(( 163,105,323,265 )).resize((160, 160)))
            frames_dict['michigan_lower'].append(original_file.copy().crop(( 279,135,439,295 )).resize((160, 160)))
            frames_dict['michigan_upper'].append(original_file.copy().crop(( 215,61,375,221 )).resize((160, 160)))
            frames_dict['minnesota'].append(original_file.copy().crop(( 52,37,262,247 )).resize((160, 160)))
            frames_dict['terre_haute'].append(original_file.copy().crop(( 208,212,368,372 )).resize((160, 160)))

            frame = frame + 1
        except EOFError:
            break
        
    
    #Write the new sets of frames to GIF files on the disk.
    for (zip_code, frame_list) in frames_dict.items():
        writeGif(
            filename=settings.MEDIA_ROOT + 'intellicast/intellicast_animated_' + zip_code + '.gif',
            images=frame_list, 
            duration=0.5,
            subRectangles=False
        )
    
    
