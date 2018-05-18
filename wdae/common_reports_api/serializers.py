'''
Created on Aug 3, 2015

@author: lubo
'''
from __future__ import unicode_literals
from rest_framework import serializers


class ChildrenCounterSerializer(serializers.Serializer):
    phenotype = serializers.CharField()
    children_male = serializers.IntegerField()
    children_female = serializers.IntegerField()
    children_unspecified = serializers.IntegerField()
    children_total = serializers.IntegerField()


class FamiliesCountersSerializer(serializers.Serializer):
    phenotype = serializers.CharField()
    counters = serializers.ListField()


class DenovoEventsCounterSerializer(serializers.Serializer):
    phenotype = serializers.CharField()
    events_count = serializers.IntegerField()
    events_children_count = serializers.IntegerField()
    events_rate_per_child = serializers.FloatField()
    events_children_percent = serializers.FloatField()


class FamilyReportSerializer(serializers.Serializer):
    phenotypes = serializers.ListField()
    children_counters = ChildrenCounterSerializer(many=True)
    families_counters = FamiliesCountersSerializer(many=True)
    families_total = serializers.IntegerField()


class DenovoEventsReportRowSerializer(serializers.Serializer):
    effect_type = serializers.CharField()
    row = serializers.ListField(child=DenovoEventsCounterSerializer())


class DenovoReportSerializer(serializers.Serializer):
    phenotypes = serializers.ListField()
    effect_groups = serializers.ListField()
    effect_types = serializers.ListField()

    rows = serializers.ListField(
        child=DenovoEventsReportRowSerializer())


class StudyVariantReportsSerializer(serializers.Serializer):
    study_name = serializers.CharField()
    study_description = serializers.CharField()
    families_report = FamilyReportSerializer()
    denovo_report = DenovoReportSerializer()
