# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Researcher'
        db.create_table('researchers', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length='100')),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length='100')),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('unique_number', self.gf('django.db.models.fields.CharField')(unique=True, max_length='100')),
        ))
        db.send_create_signal(u'api', ['Researcher'])

        # Adding model 'VerificationPath'
        db.create_table('verification_paths', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(unique=True, max_length='255')),
        ))
        db.send_create_signal(u'api', ['VerificationPath'])

        # Adding model 'WdaeUser'
        db.create_table('users', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length='100')),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length='100')),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('researcher_id', self.gf('django.db.models.fields.CharField')(max_length='100', unique=True, null=True, blank=True)),
            ('verification_path', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['api.VerificationPath'], unique=True, null=True, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'api', ['WdaeUser'])


    def backwards(self, orm):
        # Deleting model 'Researcher'
        db.delete_table('researchers')

        # Deleting model 'VerificationPath'
        db.delete_table('verification_paths')

        # Deleting model 'WdaeUser'
        db.delete_table('users')


    models = {
        u'api.researcher': {
            'Meta': {'object_name': 'Researcher', 'db_table': "'researchers'"},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': "'100'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': "'100'"}),
            'unique_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'100'"})
        },
        u'api.verificationpath': {
            'Meta': {'object_name': 'VerificationPath', 'db_table': "'verification_paths'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'255'"})
        },
        u'api.wdaeuser': {
            'Meta': {'object_name': 'WdaeUser', 'db_table': "'users'"},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': "'100'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': "'100'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'researcher_id': ('django.db.models.fields.CharField', [], {'max_length': "'100'", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'verification_path': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['api.VerificationPath']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['api']