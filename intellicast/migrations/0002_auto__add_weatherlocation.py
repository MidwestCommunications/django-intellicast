# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'WeatherLocation'
        db.create_table('intellicast_weatherlocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('intellicast_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('zipcode', self.gf('django.db.models.fields.IntegerField')(max_length=20)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=3)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=3)),
        ))
        db.send_create_signal('intellicast', ['WeatherLocation'])


    def backwards(self, orm):
        
        # Deleting model 'WeatherLocation'
        db.delete_table('intellicast_weatherlocation')


    models = {
        'intellicast.weatherlocation': {
            'Meta': {'object_name': 'WeatherLocation'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intellicast_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '3'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '3'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'zipcode': ('django.db.models.fields.IntegerField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['intellicast']
