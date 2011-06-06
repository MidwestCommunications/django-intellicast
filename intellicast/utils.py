from urllib import urlopen
from xml.dom.minidom import parse

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

        return conditions_dict, hourly_forecast_dict, daily_forecast_dict

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