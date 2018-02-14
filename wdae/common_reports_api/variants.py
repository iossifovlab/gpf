'''
Created on Jul 27, 2015

@author: lubo
'''
from collections import defaultdict, Counter
import itertools
import logging
import zlib
import cPickle

from query_prepare import EFFECT_GROUPS, build_effect_types
from DAE import vDB
import precompute
import preloaded
from common_reports_api.studies import get_denovo_studies_names, \
    get_transmitted_studies_names
from common_reports_api.permissions import get_datasets_by_study

LOGGER = logging.getLogger(__name__)


class CommonBase(object):

    @staticmethod
    def effect_types():
        et = []
        et.extend(EFFECT_GROUPS['coding'])
        et.extend(EFFECT_GROUPS['noncoding'])
        et.extend(EFFECT_GROUPS['cnv'])

        return et

    @staticmethod
    def effect_groups():
        return ['LGDs', 'nonsynonymous', 'UTRs', 'CNV']

    @staticmethod
    def family_configuration(family):
        return "".join([family[pid].role + family[pid].gender
                        for pid in sorted(family.keys(),
                                          key=lambda x: (family[x].role, x))])

class CounterBase(CommonBase):

    @staticmethod
    def build_families_buffer(studies):
        families_buffer = defaultdict(dict)
        for st in studies:
            for f in st.families.values():
                children = [f.memberInOrder[c]
                            for c in range(2, len(f.memberInOrder))]
                for p in children:
                    if p.personId in families_buffer[f.familyId]:
                        pass
                    else:
                        families_buffer[f.familyId][p.personId] = p
        return families_buffer

    def __init__(self, phenotype):
        super(CommonBase, self).__init__()
        self.phenotype = phenotype

    def filter_studies(self, all_studies):
        if self.phenotype == 'unaffected':
            return all_studies
        studies = [st for st in all_studies
                   if st.get_attr('study.phenotype') == self.phenotype]
        return studies


class ChildrenCounter(CounterBase):

    def __init__(self, phenotype):
        super(ChildrenCounter, self).__init__(phenotype)

        self.children_male = 0
        self.children_female = 0

    @property
    def children_total(self):
        return self.children_male + self.children_female

    def check_phenotype(self, person):
        if self.phenotype == 'unaffected':
            return person.role == 'sib'
        else:
            return person.role == 'prb'

    def build(self, all_studies):
        studies = self.filter_studies(all_studies)
        families_buffer = self.build_families_buffer(studies)
        children_counter = Counter()

        for family in families_buffer.values():
            for person in family.values():
                if self.check_phenotype(person):
                    children_counter[person.gender] += 1

        self.children_female = children_counter['F']
        self.children_male = children_counter['M']


class FamiliesCounters(CounterBase):

    def __init__(self, phenotype, legend):
        super(FamiliesCounters, self).__init__(phenotype)
        if phenotype == 'unaffected':
            raise ValueError("unexpected phenotype '{}'".format(phenotype))
        if phenotype not in legend:
            raise ValueError("phenotype '{}' not present in legend".format(
                phenotype))
        self.legend = legend
        self.total = 0

    def build(self, all_studies):
        studies = self.filter_studies(all_studies)
        families_buffer = self.build_families_buffer(studies)
        family_type_counter = Counter()

        for family in families_buffer.values():
            family_configuration = self.family_configuration(family)
            family_type_counter[family_configuration] += 1

        self.data = {}
        for (fconf, count) in family_type_counter.items():
            pedigree = self.family_configuration_to_pedigree_v3(fconf)
            self.data[fconf] = (pedigree, count)
            self.total += count

    def get_counter(self, fconf):
        return self.data.get(fconf, 0)

    def type_counters(self):
        return sorted(self.data.values())

    @property
    def counters(self):
        res = self.data.values()[:]
        res = sorted(res, key=lambda v: (-v[1]))
        return res

    def get_color(self, role):
        if role == 'prb':
            return self.legend[self.phenotype]
        else:
            return self.legend['unaffected']

    def family_configuration_to_pedigree_v3(self, family_configuration):
        res = [
            [
                'f1', 'p1', '', '',
                'F', self.get_color('mom'), 0, 0],
            [
                'f1', 'p2', '', '',
                'M', self.get_color('dad'), 0, 0],
        ]

        pedigree = [
            [
                family_configuration[i: i + 3],
                family_configuration[i + 3: i + 4],
            ]
            for i in range(0, len(family_configuration), 4)
        ]
        pedigree = [
            [
                'f1', 'p{}'.format(counter + 3), 'p1', 'p2',
                gender, self.get_color(role), 0, 0
            ]
            for counter, [role, gender] in enumerate(pedigree)
        ]
        res.extend(pedigree)
        return res


class ReportBase(CommonBase):

    def __init__(self, study_name):
        super(ReportBase, self).__init__()
        self.study_name = study_name
        if study_name in vDB.get_study_group_names():
            study = vDB.get_study_group(study_name)
        else:
            study = vDB.get_study(study_name)

        self.study_description = study.description

        self.studies = vDB.get_studies(self.study_name)
        self._calc_phenotypes()

    def _calc_phenotypes(self):
        dataset_ids = itertools.chain(*get_datasets_by_study(self.study_name))

        self.legend = {}
        dataset_factory = preloaded.register.get('datasets').get_factory()
        for dataset_id in dataset_ids:
            dataset = dataset_factory.get_dataset(dataset_id)
            self.legend.update({
                pheno_color['id']: pheno_color['color']
                for pheno_color in dataset.get_legend(person_grouping='phenotype')
            })

        phenotypes = self.legend.keys()
        if 'unaffected' in phenotypes:
            phenotypes.remove('unaffected')
        phenotypes.sort()
        phenotypes.append('unaffected')
        self.phenotypes = phenotypes

class FamiliesReport(ReportBase, precompute.register.Precompute):

    def __init__(self, study_name):
        super(FamiliesReport, self).__init__(study_name)
        self.families_counters = []
        self.children_counters = []
        self.families_total = 0

    def is_precomputed(self):
        return self.families_counters

    def build(self):
        self.families_total = 0
        encountered_phenotypes = []
        for phenotype in self.phenotypes[:-1]:
            assert phenotype != 'unaffected'
            fc = FamiliesCounters(phenotype, self.legend)
            fc.build(self.studies)
            if fc.total != 0:
                self.families_counters.append(fc)
                self.families_total += fc.total
                encountered_phenotypes.append(phenotype)

        self.phenotypes = encountered_phenotypes + ['unaffected']

        for phenotype in self.phenotypes:
            cc = ChildrenCounter(phenotype)
            cc.build(self.studies)
            self.children_counters.append(cc)

    def get_children_counters(self, phenotype):
        for cc in self.children_counters:
            if phenotype == cc.phenotype:
                return cc
        return None

    def get_families_counters(self, phenotype):
        for fc in self.families_counters:
            if phenotype == fc.phenotype:
                return fc
        return None

    def precompute(self):
        self.build()

    def serialize(self):
        fc = zlib.compress(cPickle.dumps(self.families_counters))
        cc = zlib.compress(cPickle.dumps(self.children_counters))
        ft = zlib.compress(cPickle.dumps(self.families_total))
        return {'families_counters': fc,
                'families_total': ft,
                'children_counters': cc}

    def deserialize(self, data):
        fc = data['families_counters']
        self.families_counters = cPickle.loads(zlib.decompress(fc))
        ft = data['families_total']
        self.families_total = cPickle.loads(zlib.decompress(ft))
        cc = data['children_counters']
        self.children_counters = cPickle.loads(zlib.decompress(cc))
        self._remove_zero_count_phenotypes()

    def _remove_zero_count_phenotypes(self):
        for index in range(0, len(self.families_counters)):
            if self.families_counters[index].total == 0:
                self.phenotypes.remove(self.families_counters[index].phenotype)
                del self.families_counters[index]

        for index in range(0, len(self.children_counters)):
            if self.children_counters[index].phenotype not in self.phenotypes:
                del self.children_counters[index]


class DenovoEventsCounter(CounterBase):

    def __init__(self, phenotype, children_counter, effect_type):
        super(DenovoEventsCounter, self).__init__(phenotype)
        assert isinstance(effect_type, str)

        self.effect_type = effect_type
        if self.phenotype != children_counter.phenotype:
            raise ValueError("wrong phenotype in children counter")
        self.children_counter = children_counter

        self.events_count = 0
        self.events_rate_per_child = 0.0
        self.events_children_count = 0
        self.events_children_percent = 0.0

    @property
    def child_type(self):
        if self.phenotype == 'unaffected':
            return 'sib'
        else:
            return 'prb'

    @property
    def effect_types_filter(self):
        return build_effect_types([self.effect_type])

    def filter_vs(self, vs):
        ret = []
        seen = set()
        for v in vs:
            hasNew = False
            for ge in v.requestedGeneEffects:
                sym = ge['sym']
                kk = str(v.familyId) + "." + sym
                if kk not in seen:
                    hasNew = True
                    seen.add(kk)
            if hasNew:
                ret.append(v)
        return ret

    def is_zeroes(self):
        return self.events_count == 0 and self.events_children_count == 0

    def build(self, all_studies):
        studies = self.filter_studies(all_studies)
        vs = vDB.get_denovo_variants(studies,
                                     inChild=self.child_type,
                                     effectTypes=self.effect_types_filter)
        vs = self.filter_vs(vs)
        self.events_count = len(vs)
        self.events_children_count = len(set(v.familyId for v in vs))
        if self.children_counter.children_total != 0:

            self.events_children_percent = \
                round((1.0 * self.events_children_count) /
                      self.children_counter.children_total, 3)

            self.events_rate_per_child = \
                round((1.0 * self.events_count) /
                      self.children_counter.children_total, 3)


class DenovoEventsReportRow(object):
    def __init__(self):
        self.row = None
        self.effect_type = None


class DenovoEventsReport(ReportBase, precompute.register.Precompute):

    def __init__(self, study_name, families_report):
        super(DenovoEventsReport, self).__init__(study_name)
        self.families_report = families_report
        self.phenotypes = families_report.phenotypes
        self.rows = {}
        self._effect_groups = super(DenovoEventsReport, self).effect_groups()
        self._effect_types = super(DenovoEventsReport, self).effect_types()

    def is_precomputed(self):
        return self.rows

    def effect_groups(self):
        return self._effect_groups

    def effect_types(self):
        return self._effect_types

    def build_row(self, effect_type):
        row = []
        for pheno in self.phenotypes:
            cc = self.families_report.get_children_counters(pheno)
            ec = DenovoEventsCounter(pheno, cc, effect_type)
            ec.build(self.studies)
            assert ec.phenotype == pheno
            row.append(ec)
        return row

    def clear_empty_rows(self):
        effect_groups = self.effect_groups()
        effect_types = self.effect_types()
        for row in self.rows:
            et = row.effect_type
            all_zeroes = True
            for ec in row.row:
                if not ec.is_zeroes():
                    all_zeroes = False
                    break
            if all_zeroes:
                if et in effect_groups:
                    effect_groups.remove(et)
                elif et in effect_types:
                    effect_types.remove(et)
        self.effect_groups = effect_groups
        self.effect_types = effect_types

    def is_empty_column(self, phenotype):
        all_zeroes = True

        for row in self.rows:
            ec = None
            for col in row.row:
                if col.phenotype == phenotype:
                    ec = col
            if ec is not None and not ec.is_zeroes():
                all_zeroes = False
                break
        return all_zeroes

    def clear_empty_columns(self):
        remove_phenotypes = []
        for phenotype in self.phenotypes:
            if self.is_empty_column(phenotype):
                remove_phenotypes.append(phenotype)
        for to_remove in remove_phenotypes:
            self.phenotypes.remove(to_remove)

    def build(self):
        rows = []
        for effect_type in self.effect_groups():
            row = DenovoEventsReportRow()
            row.row = self.build_row(effect_type)
            row.effect_type = effect_type
            rows.append(row)

        for effect_type in self.effect_types():
            row = DenovoEventsReportRow()
            row.row = self.build_row(effect_type)
            row.effect_type = effect_type
            rows.append(row)

        self.rows = rows
        self.clear_empty_rows()

    def precompute(self):
        self.build()

    def serialize(self):
        rows = zlib.compress(cPickle.dumps(self.rows))
        return {'rows': rows}

    def deserialize(self, data):
        rows = data['rows']
        self.rows = cPickle.loads(zlib.decompress(rows))
        self.clear_empty_rows()
        self.clear_empty_columns()


class StudyVariantReports(ReportBase, precompute.register.Precompute):

    def __init__(self, study_name):
        super(StudyVariantReports, self).__init__(study_name)
        self.families_report = None
        self.denovo_report = None

    def is_precomputed(self):
        return self.families_report is not None

    def has_denovo(self):
        return any([st.has_denovo for st in self.studies])

    def build(self):
        self.families_report = FamiliesReport(self.study_name)
        self.families_report.build()
        self.phenotypes = self.families_report.phenotypes

        if self.has_denovo():
            self.denovo_report = DenovoEventsReport(
                self.study_name,
                self.families_report)
            self.denovo_report.build()
        else:
            self.denovo_report = None

    def precompute(self):
        self.build()

    def serialize(self):
        return {
            'study_name': self.study_name,
            'families_report': self.families_report.serialize(),
            'denovo_report': self.denovo_report.serialize()
            if self.denovo_report else None,
        }

    def deserialize(self, data):
        assert self.study_name == data['study_name']
        self.families_report = FamiliesReport(self.study_name)
        self.families_report.deserialize(data['families_report'])
        self.phenotypes = self.families_report.phenotypes
        if 'denovo_report' in data and data['denovo_report']:
            self.denovo_report = DenovoEventsReport(self.study_name,
                                                    self.families_report)
            self.denovo_report.deserialize(data['denovo_report'])
        else:
            self.denovo_report = None


class VariantReports(precompute.register.Precompute):

    def __init__(self):
        self.data = None

    @property
    def studies(self):
        return get_denovo_studies_names() + get_transmitted_studies_names()

    def is_precomputed(self):
        return self.data is not None

    def precompute(self):
        data = {}
        for (study_name, _) in self.studies:
            sr = StudyVariantReports(study_name)
            sr.precompute()
            data[study_name] = sr
        self.data = data

    def serialize(self):
        data = {}
        for (study_name, _) in self.studies:
            sr = self.data[study_name]
            sdict = sr.serialize()
            data[study_name] = zlib.compress(cPickle.dumps(sdict))
        return data

    def deserialize(self, data):
        res = {}
        for (study_name, _) in self.studies:
            if study_name not in data:
                continue
            assert study_name in data
            sr = StudyVariantReports(study_name)
            sdict = cPickle.loads(zlib.decompress(data[study_name]))
            sr.deserialize(sdict)
            res[study_name] = sr
        self.data = res

    def __getitem__(self, study_name):
        return self.data.get(study_name, None)
