from django.db import models

# Create your models here.

class WeatherLocation(models.Model):
    intellicast_id = models.CharField(max_length=100, unique=True)
   
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.IntegerField(max_length=20)
    
    latitude = models.DecimalField(max_digits=10, decimal_places=3)
    longitude = models.DecimalField(max_digits=10, decimal_places=3)
    
    def __unicode__(self):
        return self.city + ", " + self.state + " " + \
            str(self.zipcode) + " (" + self.intellicast_id + ")"