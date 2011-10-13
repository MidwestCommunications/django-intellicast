from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings


class ViewTestCase(TestCase):
    def test_landing_page(self):
        # test normal GET
        r = self.client.get(reverse('intellicast_weather_page'))
        self.assertEqual(r.status_code, 200)

        # test GET with zipcode
        r = self.client.get(reverse('intellicast_weather_page'), {'zipcode': '54481'})
        self.assertEqual(r.status_code, 200)

        # test GET with nonexistent city name
        r = self.client.get(reverse('intellicast_weather_page'), {'zipcode': 'aoeuaoehudaotnehd'})
        self.assertEqual(r.status_code, 200)
        
        # test GET with city name
        r = self.client.get(reverse('intellicast_weather_page'), {'zipcode': 'Detroit,MI'})
        self.assertEqual(r.status_code, 200)

        # test GET with city name with space
        r = self.client.get(reverse('intellicast_weather_page'), {'zipcode': 'Detroit, MI'})
        self.assertEqual(r.status_code, 200)
