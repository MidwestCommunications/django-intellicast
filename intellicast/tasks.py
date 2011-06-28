import os
import urllib2
from PIL import Image
from celery.decorators import task
from django.conf import settings
from images2gif import writeGif

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
        '54915': [], '53085': [], '55747': [], '49036': []
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
    
    