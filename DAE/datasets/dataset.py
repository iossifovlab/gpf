'''
Created on Feb 9, 2017

@author: lubo
'''
from DAE import pheno, vDB
import itertools
from query_variants import generate_response
from common.query_base import QueryBase, GeneSymsMixin
from gene.gene_set_collections import GeneSetsCollections
from gene.weights import WeightsLoader
from datasets.family_pheno_base import FamilyPhenoQueryMixin
from pheno.pheno_regression import PhenoRegression
from collections import defaultdict


class Dataset(QueryBase, FamilyPhenoQueryMixin):
    GENE_WEIGHTS_LOADER = None
    GENE_SETS_LOADER = None

    def __init__(self, dataset_descriptor):
        self.descriptor = dataset_descriptor
        print("loading dataset <{}>; pheno db: <{}>".format(
            self.descriptor['id'],
            self.descriptor['phenoDB'],
        ))
        self.pheno_db = None
        self.families = None
        self.persons = None

        self._enrichment_families = None

        self._studies = None
        self._denovo_studies = None
        self._transmitted_studies = None
        self._children_stats = None
        self._enrichment_children_stats = None
        self._phenotypes = None

        self.load_pheno_db()

    @property
    def name(self):
        return self.descriptor['id']

    @property
    def dataset_id(self):
        return self.descriptor['id']

    @property
    def pheno_name(self):
        return self.descriptor['phenoDB']

    @property
    def pheno_id(self):
        return self.descriptor['phenoDB']

    @property
    def studies(self):
        if self._studies is None:
            if self.descriptor['studies'] is None:
                self._studies = []
            else:
                study_names = [
                    st.strip() for st in self.descriptor['studies'].split(',')
                ]
                studies = [vDB.get_studies(st) for st in study_names]
                self._studies = [
                    st for st in itertools.chain.from_iterable(studies)
                ]
        return self._studies

    @property
    def denovo_studies(self):
        if self._denovo_studies is None:
            self._denovo_studies = [
                st for st in self.studies
                if st.has_denovo
            ]
        return self._denovo_studies

#     @property
#     def enrichment_denovo_studies(self):
#         study_types = self.descriptor['enrichmentTool']['studyTypes']
#         studies = []
#         for st in self.denovo_studies:
#             if st.get_attr('study.type') in study_types:
#                 studies.append(st)
#         return studies

    @property
    def transmitted_studies(self):
        if self._transmitted_studies is None:
            self._transmitted_studies = [
                st for st in self.studies
                if st.has_transmitted
            ]
        return self._transmitted_studies

    def _get_phenotype_filter(self, safe=True, **kwargs):
        person_grouping = self.get_pedigree_selector(
            safe=safe, default=False, ** kwargs)
        if person_grouping is None:
            return None
        if person_grouping['id'] != 'phenotype':
            return None
        selected_phenotypes = person_grouping.get_checked_values(
            safe=safe, **kwargs)

        if not selected_phenotypes:
            return None
        if 'unaffected' not in selected_phenotypes:
            def f(v):
                return 'prb' in v.inChS and \
                    v.study.get_attr('study.phenotype') in selected_phenotypes
            return f

        selected_phenotypes.remove('unaffected')
        if selected_phenotypes == set():
            def fsp(v):
                return 'sib' in v.inChS
            return fsp

        def fm(v):
            return 'sib' in v.inChS or \
                v.study.get_attr('study.phenotype') in selected_phenotypes
        return fm

    def get_in_child(self, safe=True, **kwargs):
        person_grouping = self.get_pedigree_selector(
            safe=safe, default=False, ** kwargs)
        if person_grouping is not None and \
                person_grouping['id'] == 'phenotype':
            selected_phenotypes = person_grouping.get_checked_values(
                safe=safe, **kwargs)
            if not selected_phenotypes:
                return None
            if 'unaffected' not in selected_phenotypes:
                return 'prb'
            if selected_phenotypes == set(['unaffected']):
                return 'sib'
        return None

    def get_studies(self, safe=True, **kwargs):
        studies = self.studies[:]
        return self._filter_studies(studies, safe, **kwargs)

    def get_denovo_studies(self, safe=True, **kwargs):
        studies = self.denovo_studies[:]
        return self._filter_studies(studies, safe, **kwargs)

    def _filter_studies(self, studies, safe, **kwargs):
        study_types = self.get_study_types(safe=safe, **kwargs)
        if study_types is not None:
            studies = filter(
                lambda st: st.get_attr('study.type').lower() in study_types,
                studies)
        person_grouping = self.get_pedigree_selector(
            safe=safe, default=False, **kwargs)
        if person_grouping is not None and \
                person_grouping['id'] == 'phenotype':
            selected_phenotypes = person_grouping.get_checked_values(
                safe=safe, **kwargs)
            if selected_phenotypes is not None and \
                    'unaffected' not in selected_phenotypes:
                studies = filter(
                    lambda st: st.get_attr(
                        'study.phenotype') in selected_phenotypes,
                    studies
                )
        return studies

    def get_transmitted_studies(self, safe=True, **kwargs):
        studies = self.transmitted_studies[:]
        return self._filter_studies(studies, safe, **kwargs)

    @classmethod
    def get_gene_set(cls, **kwargs):
        gene_sets_collection, gene_set, gene_sets_types = \
            GeneSymsMixin.get_gene_set_query(**kwargs)
        if not gene_sets_collection or not gene_set:
            return set([])
        if gene_sets_types is None:
            gene_sets_types = []
        if cls.GENE_SETS_LOADER is None:
            cls.GENE_SETS_LOADER = GeneSetsCollections()
        genes = cls.GENE_SETS_LOADER.get_gene_set(
            gene_sets_collection, gene_set, gene_sets_types)
        return genes['syms']

    @classmethod
    def get_gene_weights(cls, **kwargs):
        weights_id, range_start, range_end = \
            GeneSymsMixin.get_gene_weights_query(**kwargs)
        if not weights_id:
            return set([])
        if weights_id not in cls.get_gene_weights_loader():
            return set([])
        weights = cls.get_gene_weights_loader()[weights_id]
        return weights.get_genes(wmin=range_start, wmax=range_end)

    @classmethod
    def get_gene_weights_loader(cls):
        if cls.GENE_WEIGHTS_LOADER is None:
            cls.GENE_WEIGHTS_LOADER = WeightsLoader()
        return cls.GENE_WEIGHTS_LOADER

    @classmethod
    def get_gene_syms(cls, **kwargs):
        result = cls.get_gene_symbols(**kwargs) | \
            cls.get_gene_weights(**kwargs) | \
            cls.get_gene_set(**kwargs)
        if result:
            return result
        else:
            return None

    def load(self):
        if self.families:
            return
        self.load_families()
        self.load_pheno_families()
        self.load_pedigree_selectors()
        self.load_pheno_columns()
        self.load_pheno_filters()
        self.load_family_filters_by_study()

    def load_pheno_db(self):
        pheno_db = None
        pheno_reg = None
        if 'phenoDB' in self.descriptor:
            pheno_id = self.descriptor['phenoDB']
            if pheno.has_pheno_db(pheno_id):
                pheno_db = pheno.get_pheno_db(pheno_id)
                pheno_reg = PhenoRegression.build(pheno_id)
        self.pheno_db = pheno_db
        self.pheno_reg = pheno_reg

    def load_families(self):
        families = {}
        for st in self.denovo_studies:
            families.update(st.families)
        for st in self.transmitted_studies:
            families.update(st.families)
        self.families = families
        self.persons = {}
        for fam in self.families.values():
            for p in fam.memberInOrder:
                p.familyId = fam.familyId
                self.persons[p.personId] = p

    def load_pheno_families(self):
        self.geno2pheno_families = defaultdict(set)
        self.pheno2geno_families = defaultdict(set)

        self.pheno_families = defaultdict(dict)
        self.pheno_persons = {}
        if not self.pheno_db:
            return

        person_df = self.pheno_db.get_persons_df()
        persons = person_df.to_dict(orient='records')
        for p in persons:
            pid = p['person_id']
            self.pheno_persons[pid] = p
            self.pheno_families[p['family_id']][pid] = p
            if pid in self.persons:
                geno_person = self.persons[pid]
                geno_fid = geno_person.familyId
                self.geno2pheno_families[geno_fid].add(p['family_id'])
                self.pheno2geno_families[p['family_id']].add(geno_fid)

    def get_geno_families(self, pheno_families):
        if not pheno_families:
            return pheno_families
        fr = [self.pheno2geno_families.get(fid, set([])) for
              fid in pheno_families]

        result = reduce(
            lambda accum, ff: accum | ff,
            fr,
            set([])
        )
        return result

    def load_pheno_columns(self):
        pheno_columns = self.get_pheno_columns()
        if pheno_columns is None:
            return

        for (role, source, attr, _) in pheno_columns:
            assert self.pheno_db.has_measure(source), \
                'missing measure {}'.format(source)
            values = self.pheno_db.get_persons_values_df(
                [source], roles=[role])
            values.dropna(inplace=True)
            for pheno_fid in values['family_id'].unique():
                fvalues = values[values.family_id == pheno_fid]
                if len(fvalues) == 0:
                    continue
                geno_fids = self.pheno2geno_families[pheno_fid]
                for fid in geno_fids:
                    geno_fam = self.families.get(fid)
                    if not geno_fam:
                        continue
                    geno_fam.atts[attr] = fvalues[source].values[0]

    def load_pheno_filters(self):
        if self.pheno_db is None:
            return
        genotype_browser = self.descriptor['genotypeBrowser']
        if genotype_browser is None:
            return

        if 'phenoFilters' not in genotype_browser:
            return
        pheno_filters = genotype_browser.get('phenoFilters', None)
        if not pheno_filters:
            return None
        for pf in pheno_filters:
            if pf['measureType'] == 'categorical':
                mf = pf['measureFilter']
                if mf['filterType'] == 'single':
                    measure_id = mf['measure']
                    measure = self.pheno_db.get_measure(measure_id)
                    mf['domain'] = measure.values_domain.split(',')

    def load_family_filters_by_study(self):
        if self.pheno_db is None:
            return
        genotype_browser = self.descriptor['genotypeBrowser']
        if genotype_browser is None:
            return

        if 'familyStudyFilters' not in genotype_browser:
            return
        family_study_filters = genotype_browser.get('familyStudyFilters', None)
        if not family_study_filters:
            return None
        for f in family_study_filters:
            mf = f['measureFilter']
            if mf['measure'] == 'studyFilter':
                mf['domain'] = [st.name for st in self.studies]
            elif mf['measure'] == 'studyTypeFilter':
                mf['domain'] = set([st.get_attr('study.type')
                                    for st in self.studies])

    def load_pedigree_selectors(self):
        pedigree_selectors = self.descriptor['pedigreeSelectors']
        if pedigree_selectors is None:
            return None
        for pedigree_selector in pedigree_selectors:
            source = pedigree_selector['source']
            if source == 'legacy':
                assert pedigree_selector['id'] == 'phenotype'
            else:
                assert self.pheno_db is not None, repr(self.descriptor)
                measure_id = source
                assert self.pheno_db.has_measure(measure_id)
                self._augment_pedigree_selector(
                    pedigree_selector, measure_id)

    def _augment_pedigree_selector(self, pedigree_selector, measure_id):
        assert self.families
        pedigree_id = pedigree_selector['id']
        default_value = pedigree_selector['default']['id']

        measure_values = self.pheno_db.get_measure_values(
            measure_id,
            person_ids=self.persons.keys())
        for p in self.persons.values():
            value = measure_values.get(p.personId, default_value)
            p.atts[pedigree_id] = value

    def get_pedigree_selector(self, default=True, **kwargs):
        pedigrees = self.descriptor['pedigreeSelectors']
        pedigree_selector_request = kwargs.get('pedigreeSelector', None)
        if pedigree_selector_request:
            assert 'id' in kwargs['pedigreeSelector']
            selector_id = kwargs['pedigreeSelector']['id']
            return self.idlist_get(pedigrees, selector_id)
        elif 'person_grouping' in kwargs:
            return self.idlist_get(pedigrees, kwargs['person_grouping'])
        if default:
            return pedigrees[0]

        return None

    def get_phenotypes(self):
        if self._phenotypes is None:
            phenotype_selector = self.get_pedigree_selector(
                person_grouping='phenotype')
            result = [
                p['id'] for p in phenotype_selector.domain
            ]
            self._phenotypes = result
        return self._phenotypes

    def filter_families_by_pedigree_selector(self, **kwargs):
        if not kwargs.get('pedigreeSelector', None) and \
                not kwargs.get('person_grouping', None):
            return None

        pedigree = self.get_pedigree_selector(**kwargs)
        pedigree_id = pedigree.id

        if pedigree_id == 'phenotype':
            return None

        pedigree_checked_values = pedigree.get_checked_values(**kwargs)
        if pedigree_checked_values is None:
            return None
        family_ids = set([])
        for fid, fam in self.families.items():
            for p in fam.memberInOrder[2:]:
                if p.atts[pedigree_id] in pedigree_checked_values:
                    family_ids.add(fid)
                    continue
        return family_ids

    def get_family_ids(self, safe=True, **kwargs):
        family_filters = [
            super(Dataset, self).get_family_ids(**kwargs),
            self.filter_families_by_pedigree_selector(**kwargs),
        ]
        if self.pheno_db:
            pheno_filters = self.get_family_pheno_filters(safe=safe, **kwargs)
            family_filters.extend(pheno_filters)

        family_filters = [ff for ff in family_filters if ff is not None]
        if not family_filters:
            return None
        assert all([isinstance(ff, set) for ff in family_filters])

        family_ids = reduce(
            lambda f1, f2: f1 & f2,
            family_filters
        )
        #         if not family_ids:
        #             return None
        return list(family_ids)

    def get_denovo_filters(self, safe=True, **kwargs):
        return {
            'geneSyms': self.get_gene_syms(
                safe=safe,
                **kwargs),
            'effectTypes': self.get_effect_types(
                safe=safe,
                **kwargs),
            'variantTypes': self.get_variant_types(
                safe=safe,
                **kwargs),
            'gender': self.get_child_gender(
                safe=safe,
                **kwargs),
            'presentInParent': self.get_present_in_parent(
                safe=safe,
                **kwargs),
            'presentInChild': self.get_present_in_child(
                safe=safe,
                **kwargs),
            'roles': self.get_roles_filter(safe=safe, **kwargs),
            'inChild': self.get_in_child(
                safe=safe,
                **kwargs),
            'regionS': self.get_regions(
                safe=safe,
                **kwargs),
            'familyIds': self.get_family_ids(
                safe=safe,
                **kwargs),
            'genomicScores': self.get_genomic_scores(
                safe=safe,
                **kwargs)
        }

    def get_transmitted_filters(self, safe=True, **kwargs):
        filters = self.get_denovo_filters(safe=safe, **kwargs)
        transmitted_filters = {
            'ultraRareOnly': self.get_ultra_rare(
                safe=safe, **kwargs),
            'minAltFreqPrcnt': self.get_min_alt_freq(
                safe=safe, **kwargs),
            'maxAltFreqPrcnt': self.get_max_alt_freq(
                safe=safe, **kwargs),
            'minParentsCalled': self.get_min_parents_called(
                safe=safe, **kwargs),
            'limit': self.get_limit(
                safe=safe, **kwargs),
            'TMM_ALL': False,
        }
        filters.update(transmitted_filters)
        return filters

    def get_denovo_variants(self, safe=True, **kwargs):
        denovo_filters = self.get_denovo_filters(safe, **kwargs)
        if denovo_filters.get('familyIds', None) == []:
            raise StopIteration()
        seen_vs = set()
        for st in self.get_denovo_studies(safe=safe, **kwargs):
            for v in st.get_denovo_variants(**denovo_filters):
                v_key = v.familyId + v.location + v.variant
                if v_key in seen_vs:
                    continue
                yield v
                seen_vs.add(v_key)

    def get_transmitted_variants(self, safe=True, **kwargs):
        transmitted_filters = self.get_transmitted_filters(safe=safe, **kwargs)
        if transmitted_filters.get('familyIds', None) == []:
            raise StopIteration()
        present_in_parent = transmitted_filters.get('presentInParent', None)
        if present_in_parent and present_in_parent == ['neither']:
            return

        for st in self.get_transmitted_studies(safe=safe, **kwargs):
            for v in st.get_transmitted_variants(**transmitted_filters):
                yield v

    def get_variants(self, safe=True, **kwargs):
        denovo = self.get_denovo_variants(safe=safe, **kwargs)
        transmitted = self.get_transmitted_variants(safe=safe, **kwargs)
        augment_vars = self._get_var_augmenter(safe=safe, **kwargs)
        variants = itertools.imap(augment_vars,
            itertools.chain.from_iterable([denovo, transmitted]))
        return self._phenotype_filter(variants, **kwargs)

    def get_legend(self, **kwargs):
        legend = self.get_pedigree_selector(**kwargs)
        response = legend.domain[:]
        response.append(legend.default)
        return response


    def _phenotype_filter(self, variants, **kwargs):
        phenotype_filter = self._get_phenotype_filter(**kwargs)
        if phenotype_filter is None:
            for v in variants:
                yield v
        else:
            for v in variants:
                if phenotype_filter(v):
                    yield v

    def get_columns(self, matches=None):
        return [key for (key, _) in self.get_genotype_columns(matches)] + \
            [key for (_, _, key, _) in self.get_pheno_columns(matches)]

    def __get_columns_for(self, view_type):
        gb = self.descriptor['genotypeBrowser']
        if gb is None:
            return self.get_columns()
        columns = gb[view_type + 'Columns']
        return self.get_columns(lambda column: column['id'] in columns)

    def get_preview_columns(self):
        return self.__get_columns_for('preview')

    def get_download_columns(self):
        return self.__get_columns_for('download')

    def get_column_labels(self):
        column_labels = { key: label for (key, label) in self.get_genotype_columns() }
        column_labels.update({ key: label for (_, _, key, label) in self.get_pheno_columns() })
        return  column_labels

    def get_pheno_columns(self, matches=None):
        gb = self.descriptor['genotypeBrowser']
        if gb is None:
            return None

        pheno_columns = gb.get('phenoColumns', [])
        if not pheno_columns:
            return []
        if matches:
            pheno_columns = filter(matches, pheno_columns)
        columns = []
        for pheno_column in pheno_columns:
            name = pheno_column['name']
            slots = pheno_column['slots']
            columns.extend([
                (s['role'], s['source'], s['id'], '{} {}'.format(name, s['name']))
                for s in slots])
        return columns

    def get_genotype_columns(self, matches=None):
        gb = self.descriptor['genotypeBrowser']
        if gb is None:
            return None

        geno_columns = gb.get('genotypeColumns', [])
        if not geno_columns:
            return []
        if matches:
            geno_columns = filter(matches, geno_columns)
        columns = []
        for geno_column in geno_columns:
            slots = geno_column['slots']
            columns.extend([
                (s['source'], s['name'])
                for s in slots])
            if geno_column.get('source', None):
                columns.append((geno_column['source'], geno_column['name']))
        return columns

    def get_variants_preview(self, safe=True, **kwargs):
        return generate_response(self.get_variants(safe, **kwargs),
            self.get_columns(), self.get_column_labels())

    def _get_var_augmenter(self, safe=True, **kwargs):
        legend = self.get_pedigree_selector(**kwargs)
        pheno_columns = self.get_pheno_columns()
        genotype_columns = self.get_genotype_columns()
        genotype_column_keys = {key for (key, _) in genotype_columns}

        families = {}
        if pheno_columns and self.pheno_db:
            families = self.families

        gene_weights = {key: value.to_dict()
                        for key, value
                        in self.get_gene_weights_loader().weights.items()
                        if key in genotype_column_keys}

        def augment_vars(v):
            chProf = "".join((p.role.name + p.gender for p in v.memberInOrder[2:]))

            v.atts["_ch_prof_"] = chProf
            v.atts["pedigree"] = v.pedigree_v3(legend)
            family = families.get(v.familyId, None)
            fatts = family.atts if family else {}
            for (_, _, key, _) in pheno_columns:
                v.atts[key] = fatts.get(key, '')

            v._phenotype_ = v.study.get_attr('study.phenotype')

            for key, value in gene_weights.items():
                genes = {effect['sym'] for effect in v.geneEffect}
                values = [value[gene] for gene in genes if gene in value]
                if len(values) > 0:
                    v.atts[key] = min(values)
            return v

        return augment_vars
