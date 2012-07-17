import os
from datetime import timedelta
from PIL import Image
from celery.decorators import task
from django.conf import settings
from django.core.cache import cache
from images2gif import writeGif
from tempfile import mkstemp

import requests
from StringIO import StringIO
from xml.dom.minidom import parse, parseString
from django.contrib.sites.models import Site
from django.core.exceptions import FieldError
from django.utils import timezone

from intellicast.utils import get_intellicast_data

@task(name='intellicast.fetch_intellicast_data')
def prefetch_intellicast_data():
    try:
        site_zip_codes = Site.objects.values_list('profile__zip_code', flat=True)
    except FieldError:
        site_zip_codes = settings.INTELLICAST_PREFETCH_ZIPS

    now = timezone.now()
    for zipcode in site_zip_codes:
        if zipcode == '':
            continue
        intellicast_data = get_intellicast_data(zipcode, False, True)
        if not all(intellicast_data):
            last_success_time = cache.get('intellicast_fetch_success')
            if not last_success_time or now - last_success_time > timedelta(hours=1):
                cache.set('intellicast_fetch_success', now, 60 * 60 * 2)
                raise Exception('Intellicast seems to be down.')
            break
    else:
        cache.set('intellicast_fetch_success', now, 60 * 60 * 2)


@task(name='intellicast.update_map_images')
def update_map_images():
    #Fetch a radar image of the Midwest from Intellicast and save it to disk.
    r = requests.get('http://services.intellicast.com/200904-01/158765827/Image/Radar/Radar2009.13L/Loop/SectorName/r03')
    
    #Load up the fetched file from the disk
    original_file = Image.open(StringIO(r.content))
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
            filename=settings.MEDIA_ROOT + '/intellicast/intellicast_animated_' + zip_code + '.gif',
            images=frame_list, 
            duration=0.5,
            subRectangles=False
        )
    
    
