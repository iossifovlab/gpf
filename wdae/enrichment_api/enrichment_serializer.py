'''
Created on May 4, 2017

@author: lubo
'''
from enrichment_api.enrichment_builder import EnrichmentBuilder
from enrichment_tool.event_counters import EnrichmentResult
from common.query_base import EffectTypesMixin, ChildGenderMixin


class EnrichmentSerializer(EffectTypesMixin, ChildGenderMixin):

    def __init__(self, results):
        self.enrichment_results = results

    def serialize(self):
        assert self.enrichment_results is not None
        output = []
        for results in self.enrichment_results:
            output.append(self.serialize_person_grouping(results))
        return output

    def serialize_person_grouping(self, grouping_results):
        output = {}
        output['selector'] = grouping_results['selector']
        output['personGroupingId'] = grouping_results['personGroupingId']

        for effect_type in EnrichmentBuilder.EFFECT_TYPES:
            result = grouping_results[effect_type]
            out = {}
            out['all'] = self.serialize_all(
                grouping_results, effect_type, result['all'])
            out['rec'] = self.serialize_rec(
                grouping_results, effect_type, result['rec'])
            out['male'] = self.serialize_male(
                grouping_results, effect_type, result['male'])
            out['female'] = self.serialize_female(
                grouping_results, effect_type, result['female'])
            output[effect_type] = out
        return output

    def serialize_common_filter(
            self, grouping_results, effect_type, gender=['male', 'female']):

        common_filter = {
            'effectTypes': [self.build_effect_types(effect_type)],
            'gender': gender,
            'pedigreeSelector': {
                'id': grouping_results['personGroupingId'],
                'checkedValues': [grouping_results['personGroupingValue']]},
            'studyTypes': ['we'],
            'variantTypes': ['ins', 'sub', 'del']
        }
        return common_filter

    def serialize_overlap_filter(
            self, grouping_results, effect_type, gender=['male', 'female']):
        common_filter = self.serialize_common_filter(
            grouping_results, effect_type, gender=gender)
        common_filter['geneSymbols'] = grouping_results['geneSymbols']
        return common_filter

    def serialize_all(self, grouping_results, effect_type, result):
        assert result.name == 'all'
        return self._serialize_gender_filter(
            grouping_results, effect_type, result)

    def serialize_male(self, grouping_results, effect_type, result):
        assert result.name == 'male'
        return self._serialize_gender_filter(
            grouping_results, effect_type, result)

    def serialize_female(self, grouping_results, effect_type, result):
        assert result.name == 'female'
        return self._serialize_gender_filter(
            grouping_results, effect_type, result)

    def _serialize_gender_filter(self, grouping_results, effect_type, result):
        assert result.name in set(['all', 'male', 'female'])
        gender = self.build_child_gender(result.name)
        output = self.serialize_enrichment_result(result)
        output['countFilter'] = self.serialize_common_filter(
            grouping_results, effect_type, gender=gender)
        output['overlapFilter'] = self.serialize_overlap_filter(
            grouping_results, effect_type, gender=gender)
        return output

    def serialize_rec(self, grouping_results, effect_type, result):
        output = self.serialize_enrichment_result(result)
        return output

    def serialize_enrichment_result(self, result):
        assert isinstance(result, EnrichmentResult)
        res = {}
        res['name'] = result.name
        res['count'] = len(result.events)
        res['overlapped'] = len(result.overlapped)
        res['expected'] = result.expected
        res['pvalue'] = result.pvalue
        return res
