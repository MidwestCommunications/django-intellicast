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
    frames_dict = {}
    #Loop through the frames of the original images, cropping out frames for each region
    while True:
        try:
            original_file.seek(frame)

            for size, key_dict in settings.INTELLICAST_CROP_DICT.items():
                for key, crop in key_dict.items():
                    frame_list = frames_dict.setdefault(key, [])
                    frame_list.append(original_file.copy().crop(crop).resize(size))

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
    
    
