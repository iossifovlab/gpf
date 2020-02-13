import math
import functools
import itertools
import traceback
import numpy as np
from copy import deepcopy

from dae.utils.variant_utils import mat2str
from dae.utils.dae_utils import split_iterable, join_line, \
    members_in_order_get_family_structure
from dae.utils.effect_utils import expand_effect_types, ge2str, gd2str, \
    gene_effect_get_worst_effect, gene_effect_get_genes

from dae.RegionOperations import Region
from dae.pheno.common import MeasureType
from dae.pheno_tool.pheno_common import PhenoFilterBuilder
from dae.variants.attributes import Role
from dae.backends.attributes_query import role_query, variant_type_converter, \
    sex_converter, AndNode, NotNode, OrNode, ContainsNode

from dae.configuration.gpf_config_parser import GPFConfigParser


class StudyWrapper(object):

    def __init__(self, genotype_data_study, pheno_db,
                 gene_weights_db, *args, **kwargs):
        super(StudyWrapper, self).__init__(*args, **kwargs)
        assert genotype_data_study is not None

        self.genotype_data_study = genotype_data_study
        self.config = genotype_data_study.config
        assert self.config is not None

        self._init_wdae_config()
        self.pheno_db = pheno_db
        self._init_pheno(self.pheno_db)

        self.gene_weights_db = gene_weights_db

    def _init_wdae_config(self):
        genotype_browser_config = self.config.genotype_browser
        if not genotype_browser_config:
            return

        # PHENO
        pheno_column_slots = []
        if genotype_browser_config.pheno:
            for col_id, pheno_col in genotype_browser_config.pheno.field_values_iterator():
                for slot in pheno_col.slots:
                    slot = GPFConfigParser.modify_tuple(
                        slot, {"id": f"{col_id}.{slot.name}"}
                    )
                    pheno_column_slots.append(slot)
        self.pheno_column_slots = pheno_column_slots or []

        # PHENO FILTERS
        self.pheno_filters = genotype_browser_config.pheno_filters or []

        # GENE WEIGHTS
        self.gene_weight_column_sources = [
            slot.source
            for slot
            in (genotype_browser_config.genotype.weights.slots or [])
        ]

        # IN ROLE
        self.in_role_columns = genotype_browser_config.in_roles or []

        # PRESENT IN ROLE
        self.present_in_role = genotype_browser_config.present_in_role or []

        # PEOPLE GROUP
        self.people_group = self.config.people_group or {}

        # LEGEND
        if len(self.people_group) != 0:
            def pg_to_dict(pg):
                return [
                    GPFConfigParser._namedtuple_to_dict(domain)
                    for domain in pg.domain + [pg.default]
                ]
            self.legend = {
                pg_id: pg_to_dict(pg)
                for pg_id, pg in self.people_group.field_values_iterator()
                if hasattr(pg, "domain")
            }
        else:
            self.legend = {}

        # PREVIEW AND DOWNLOAD COLUMNS
        preview_column_names = genotype_browser_config.preview_columns
        download_column_names = genotype_browser_config.download_columns

        def unpack_columns(selected_columns, use_id=True):
            columns, sources = [], []

            def inner(cols):
                for col_id, col in cols.field_values_iterator():
                    if col_id not in selected_columns:
                        continue
                    if col.source is not None:
                        columns.append(col_id if use_id else col.name)
                        sources.append(col.source)
                    if col.slots is not None:
                        for slot in col.slots:
                            columns.append(f"{col_id}.{slot.name}"
                                           if use_id else f"{slot.name}")
                            sources.append(slot.source)
            inner(genotype_browser_config.genotype)
            if genotype_browser_config.pheno:
                inner(genotype_browser_config.pheno)
            return columns, sources

        if genotype_browser_config.genotype:
            self.preview_columns, self.preview_sources = \
                unpack_columns(preview_column_names)
            self.download_columns, self.download_sources = \
                unpack_columns(download_column_names, use_id=False)
        else:
            self.preview_columns, self.preview_sources = [], []
            self.download_columns, self.download_sources = [], []

    def _init_pheno(self, pheno_db):
        self.phenotype_data = None
        self.pheno_filter_builder = None

        self.pheno_filters_in_config = set()
        phenotype_data = self.config.phenotype_data
        if phenotype_data:
            self.phenotype_data = pheno_db.get_phenotype_data(phenotype_data)

            if self.pheno_filters:
                self.pheno_filters_in_config = {
                    f'{f.role}.{f.measure}'
                    for pf in self.pheno_filters
                    for f in pf.filter
                    if f.measure and f.filter_type == 'single'
                }
                self.pheno_filter_builder = PhenoFilterBuilder(
                    self.phenotype_data
                )

    def __getattr__(self, name):
        return getattr(self.genotype_data_study, name)

    FILTER_RENAMES_MAP = {
        'familyIds': 'family_ids',
        'gender': 'sexes',
        'geneSymbols': 'genes',
        'variantTypes': 'variant_type',
        'effectTypes': 'effect_types',
        'regionS': 'regions',
    }

    STANDARD_ATTRS = {
        'family': 'family_id',
        'location': 'cshl_location',
        'variant': 'cshl_variant',
    }

    STANDARD_ATTRS_LAMBDAS = {
        key: lambda aa, val=val: getattr(aa, val)
        for key, val in STANDARD_ATTRS.items()
    }

    SPECIAL_ATTRS_FORMAT = {
        'genotype': lambda aa: mat2str(aa.genotype),
        'effects': lambda aa: ge2str(aa.effect),
        'genes': lambda aa: gene_effect_get_genes(aa.effect),
        'worst_effect': lambda aa: gene_effect_get_worst_effect(aa.effect),
        'effect_details': lambda aa: gd2str(aa.effect),
        'best_st': lambda aa: mat2str(aa.best_st),
        'family_structure': lambda aa:
            members_in_order_get_family_structure(aa.members_in_order)
    }

    SPECIAL_ATTRS = {
        **SPECIAL_ATTRS_FORMAT,
        **STANDARD_ATTRS_LAMBDAS
    }

    def generate_pedigree(self, allele, people_group):
        result = []
        best_st = np.sum(allele.gt == allele.allele_index, axis=0)

        for index, member in enumerate(allele.members_in_order):
            result.append(
                self._get_wdae_member(member, people_group, best_st[index])
            )

        return result

    def query_list_variants(self, sources, people_group, **kwargs):
        for v in self.query_variants(**kwargs):
            for aa in v.matched_alleles:
                assert not aa.is_reference_allele

                row_variant = []
                for source in sources:
                    try:
                        if source in self.SPECIAL_ATTRS:
                            row_variant.append(self.SPECIAL_ATTRS[source](aa))
                        elif source == 'pedigree':
                            row_variant.append(
                                self.generate_pedigree(aa, people_group)
                            )
                        else:
                            attribute = aa.get_attribute(source, '')

                            if not isinstance(attribute, str) and \
                                    not isinstance(attribute, list):
                                if attribute is None or math.isnan(attribute):
                                    attribute = ''
                                elif math.isinf(attribute):
                                    attribute = 'inf'

                            row_variant.append(attribute)

                    except (AttributeError, KeyError):
                        traceback.print_exc()
                        row_variant.append('')

                yield row_variant

    def get_variant_web_rows(self, query, sources, max_variants_count=None):
        people_group_id = query.get('peopleGroup', {}).get('id', None)
        people_group = self.get_families_group(people_group_id)

        rows = self.query_list_variants(sources, people_group, **query)

        if max_variants_count is not None:
            limited_rows = itertools.islice(rows, max_variants_count)

        return limited_rows

    def get_wdae_preview_info(self, query, max_variants_count=1000):
        preview_info = {}

        preview_info['cols'] = self.preview_columns
        preview_info['legend'] = self.get_legend(**query)

        preview_info['maxVariantsCount'] = max_variants_count

        return preview_info

    def get_variants_wdae_preview(self, query, max_variants_count=1000):
        variants_data = self.get_variant_web_rows(
            query, self.preview_sources,
            max_variants_count=(max_variants_count + 1)
        )

        return variants_data

    def get_variants_wdae_download(self, query, max_variants_count=10000):
        rows = self.get_variant_web_rows(
            query, self.download_sources, max_variants_count=max_variants_count
        )

        wdae_download = map(
            join_line, itertools.chain([self.download_columns], rows)
        )

        return wdae_download

    # Not implemented:
    # callSet
    # minParentsCalled
    # ultraRareOnly
    # TMM_ALL
    def query_variants(self, **kwargs):
        # print("kwargs in study group:", kwargs)
        kwargs = self._add_people_with_people_group(kwargs)

        limit = None
        if 'limit' in kwargs:
            limit = kwargs['limit']

        if 'regions' in kwargs:
            kwargs['regions'] = list(map(Region.from_str, kwargs['regions']))

        if 'presentInChild' in kwargs:
            self._transform_present_in_child(kwargs)

        if 'presentInParent' in kwargs:
            self._transform_present_in_parent(kwargs)

        if 'presentInRole' in kwargs:
            self._transform_present_in_role(kwargs)

        if 'minAltFrequencyPercent' in kwargs or \
                'maxAltFrequencyPercent' in kwargs:
            self._transform_min_max_alt_frequency(kwargs)

        if 'genomicScores'in kwargs:
            self._transform_genomic_scores(kwargs)

        if 'geneWeights' in kwargs:
            self._transform_gene_weights(kwargs)

        for key in list(kwargs.keys()):
            if key in self.FILTER_RENAMES_MAP:
                kwargs[self.FILTER_RENAMES_MAP[key]] = kwargs[key]
                kwargs.pop(key)

        if 'sexes' in kwargs:
            sexes = set(kwargs['sexes'])
            if sexes != set(['female', 'male', 'unspecified']):
                sexes = [ContainsNode(sex_converter(sex)) for sex in sexes]
                kwargs['sexes'] = OrNode(sexes)
            else:
                kwargs['sexes'] = None

        if 'variant_type' in kwargs:
            variant_types = set(kwargs['variant_type'])
            if variant_types != {'ins', 'del', 'sub'}:
                variant_types = [
                    ContainsNode(variant_type_converter(t))
                    for t in variant_types]
                kwargs['variant_type'] = OrNode(variant_types)
            else:
                kwargs['variant_type'] = None

        if 'effect_types' in kwargs:
            kwargs['effect_types'] = expand_effect_types(
                kwargs['effect_types'])

        if 'studyFilters' in kwargs:
            if kwargs['studyFilters']:
                kwargs['study_filters'] =\
                    [sf['studyName'] for sf in kwargs['studyFilters']]
            else:
                del(kwargs['studyFilters'])

        if 'phenoFilters' in kwargs:
            kwargs = self._transform_pheno_filter(kwargs)
            if kwargs is None:
                return

        if 'person_ids' in kwargs:
            kwargs['person_ids'] = list(kwargs['person_ids'])

        if 'inheritanceTypeFilter' in kwargs:
            kwargs['inheritance'] = \
                'any({})'.format(','.join(kwargs['inheritanceTypeFilter']))
            kwargs.pop('inheritanceTypeFilter')

        variants_from_studies = itertools.islice(
            self.genotype_data_study.query_variants(**kwargs), limit)

        for variant in self._add_additional_columns(variants_from_studies):
            yield variant

    def _add_additional_columns(self, variants_iterable):
        for variants_chunk in split_iterable(variants_iterable, 5000):
            families = {variant.family_id for variant in variants_chunk}

            pheno_column_values = self._get_all_pheno_values(families)

            for variant in variants_chunk:
                pheno_values = self._get_pheno_values_for_variant(
                    variant, pheno_column_values
                )

                for allele in variant.alt_alleles:
                    roles_values = self._get_all_roles_values(allele)
                    gene_weights_values = self._get_gene_weights_values(allele)

                    if pheno_values:
                        allele.update_attributes(pheno_values)

                    if roles_values:
                        allele.update_attributes(roles_values)

                    allele.update_attributes(gene_weights_values)

                yield variant

    def _get_pheno_values_for_variant(self, variant, pheno_column_values):
        if not pheno_column_values:
            return None

        pheno_values = {}

        for pheno_column_df, pheno_column_name in pheno_column_values:
            variant_pheno_value_df = pheno_column_df[
                pheno_column_df['person_id'].isin(variant.members_ids)]
            variant_pheno_value_df.set_index('person_id', inplace=True)
            assert len(variant_pheno_value_df.columns) == 1
            column = variant_pheno_value_df.columns[0]

            pheno_values[pheno_column_name] = \
                list(variant_pheno_value_df[column].map(str).tolist())

        return pheno_values

    def _get_all_pheno_values(self, families):
        if not self.phenotype_data or not self.pheno_column_slots:
            return None

        pheno_column_names = []
        pheno_column_dfs = []

        for slot in self.pheno_column_slots:
            pheno_column_names.append(slot.source)
            pheno_column_dfs.append(
                self.phenotype_data.get_measure_values_df(
                    slot.source,
                    family_ids=list(families),
                    roles=[slot.role]))

        return list(zip(pheno_column_dfs, pheno_column_names))

    def _get_gene_weights_values(self, allele):
        if not self.gene_weight_column_sources:
            return {}
        genes = gene_effect_get_genes(allele.effects).split(';')
        gene = genes[0]

        gene_weights_values = {}
        for gwc in self.gene_weight_column_sources:
            if gwc not in self.gene_weights_db:
                continue

            gene_weights = self.gene_weights_db[gwc]
            if gene != '':
                gene_weights_values[gwc] =\
                    gene_weights._to_dict().get(gene, '')
            else:
                gene_weights_values[gwc] = ''

        return gene_weights_values

    def _get_all_roles_values(self, allele):
        if not self.in_role_columns:
            return None

        result = {}
        for roles_value in self.in_role_columns:
            result[roles_value.destination] = \
                "".join(self._get_roles_value(allele, roles_value.roles))

        return result

    def _get_roles_value(self, allele, roles):
        result = []
        variant_in_members = allele.variant_in_members_objects
        for role in roles:
            for member in variant_in_members:
                role = Role.from_name(role)
                if member.role == role:
                    result.append(str(role) + member.sex.short())

        return result

    def _merge_with_people_ids(self, kwargs, people_ids_to_query):
        people_ids_filter = kwargs.pop('person_ids', None)
        result = people_ids_to_query
        if people_ids_filter is not None:
            result = people_ids_to_query.intersection(people_ids_filter)

        return result

    def _get_pheno_filter_constraints(self, pheno_filter):
        measure_type = MeasureType.from_str(pheno_filter['measureType'])
        selection = pheno_filter['selection']
        if measure_type in (MeasureType.continuous, MeasureType.ordinal):
            return tuple([selection['min'], selection['max']])
        return set(selection['selection'])

    def _add_people_with_people_group(self, kwargs):

        if 'peopleGroup' not in kwargs or kwargs['peopleGroup'] is None:
            return kwargs

        people_group_query = kwargs.pop('peopleGroup')
        people_group_id = people_group_query['id']
        people_group_values = set(people_group_query['checkedValues'])

        families_group = self.genotype_data_study.get_families_group(
            people_group_id
        )
        if not families_group:
            return kwargs

        if set(families_group.domain) == people_group_values:
            return kwargs

        persons = families_group.get_people_with_propvalues(
            tuple(people_group_values))
        person_ids = set([p.person_id for p in persons])

        if 'person_ids' in kwargs:
            person_ids.intersection(set(kwargs['person_ids']))

        kwargs['person_ids'] = list(person_ids)

        return kwargs

    def _transform_genomic_scores(self, kwargs):
        genomic_scores = kwargs.pop('genomicScores', [])

        genomic_scores_filter = [
            (score['metric'],
             (score['rangeStart'], score['rangeEnd']))
            for score in genomic_scores
            if score['rangeStart'] or score['rangeEnd']
        ]

        if 'real_attr_filter' not in kwargs:
            kwargs['real_attr_filter'] = []
        kwargs['real_attr_filter'] += genomic_scores_filter

    def _transform_gene_weights(self, kwargs):
        if not self.gene_weights_db:
            return

        gene_weights = kwargs.pop('geneWeights', {})

        weight_name = gene_weights.get('weight', None)
        range_start = gene_weights.get('rangeStart', None)
        range_end = gene_weights.get('rangeEnd', None)

        if weight_name and weight_name in self.gene_weights_db:
            weight = self.gene_weights_db[gene_weights.get('weight')]

            genes = weight.get_genes(range_start, range_end)

            if 'genes' not in kwargs:
                kwargs['genes'] = []

            kwargs['genes'] += list(genes)

    def _transform_min_max_alt_frequency(self, kwargs):
        min_value = None
        max_value = None

        if 'minAltFrequencyPercent' in kwargs:
            min_value = kwargs['minAltFrequencyPercent']
            kwargs.pop('minAltFrequencyPercent')

        if 'maxAltFrequencyPercent' in kwargs:
            max_value = kwargs['maxAltFrequencyPercent']
            kwargs.pop('maxAltFrequencyPercent')

        value_range = (min_value, max_value)

        if value_range == (None, None):
            return

        if value_range[0] is None:
            value_range = (float('-inf'), value_range[1])

        if value_range[1] is None:
            value_range = (value_range[0], float('inf'))

        value = 'af_allele_freq'
        if 'real_attr_filter' not in kwargs:
            kwargs['real_attr_filter'] = []

        kwargs['real_attr_filter'].append((value, value_range))

    def _transform_present_in_child(self, kwargs):
        roles_query = []

        for filter_option in kwargs['presentInChild']:
            new_roles = None

            if filter_option == 'proband only':
                new_roles = AndNode([
                    ContainsNode(Role.prb),
                    NotNode(ContainsNode(Role.sib))
                ])

            if filter_option == 'sibling only':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.prb)),
                    ContainsNode(Role.sib)
                ])

            if filter_option == 'proband and sibling':
                new_roles = AndNode([
                    ContainsNode(Role.prb),
                    ContainsNode(Role.sib)
                ])

            if filter_option == 'neither':
                new_roles = AndNode([
                    NotNode(ContainsNode(Role.prb)),
                    NotNode(ContainsNode(Role.sib))
                ])

            if new_roles:
                roles_query.append(new_roles)

        kwargs.pop('presentInChild')

        self._add_roles_to_query(roles_query, kwargs)

    def _transform_present_in_parent(self, kwargs):
        roles_query = []
        present_in_parent = set(kwargs['presentInParent']['presentInParent'])
        rarity = kwargs['presentInParent'].get('rarity', None)

        if present_in_parent != set([
                'father only', 'mother only', 'mother and father', 'neither']):

            for filter_option in present_in_parent:
                new_roles = None

                if filter_option == 'mother only':
                    new_roles = AndNode([
                        NotNode(ContainsNode(Role.dad)),
                        ContainsNode(Role.mom)
                    ])

                if filter_option == 'father only':
                    new_roles = AndNode([
                        ContainsNode(Role.dad),
                        NotNode(ContainsNode(Role.mom))
                    ])

                if filter_option == 'mother and father':
                    new_roles = AndNode([
                        ContainsNode(Role.dad),
                        ContainsNode(Role.mom)
                    ])

                if filter_option == 'neither':
                    new_roles = AndNode([
                        NotNode(ContainsNode(Role.dad)),
                        NotNode(ContainsNode(Role.mom))
                    ])

                if new_roles:
                    roles_query.append(new_roles)
        self._add_roles_to_query(roles_query, kwargs)

        if rarity is not None:
            ultra_rare = rarity.get('ultraRare', None)
            ultra_rare = bool(ultra_rare)
            if ultra_rare and present_in_parent != {'neither'}:
                kwargs['ultra_rare'] = True
            else:
                max_alt_freq = rarity.get('maxFreq', None)
                min_alt_freq = rarity.get('minFreq', None)
                if min_alt_freq is not None or max_alt_freq is not None:
                    real_attr_filter = kwargs.get('real_attr_filter', [])
                    real_attr_filter.append(
                        ('af_allele_freq', (min_alt_freq, max_alt_freq))
                    )
                    kwargs['real_attr_filter'] = real_attr_filter
        kwargs.pop('presentInParent')

    def _transform_present_in_role(self, kwargs):
        roles_query = []

        for pir_id, filter_options in kwargs['presentInRole'].items():

            for filter_option in filter_options:
                new_roles = None

                if filter_option != 'neither':
                    new_roles = \
                        ContainsNode(Role.from_name(filter_option))

                if filter_option == 'neither':
                    new_roles = AndNode([
                        NotNode(ContainsNode(Role.from_name(role)))
                        for role in self.get_present_in_role(pir_id).roles
                    ])

                if new_roles:
                    roles_query.append(new_roles)

        kwargs.pop('presentInRole')

        self._add_roles_to_query(roles_query, kwargs)

    def _transform_pheno_filters_to_people_ids(self, pheno_filter_args):
        people_ids = []
        for pheno_filter_arg in pheno_filter_args:
            if not self.phenotype_data.has_measure(
                    pheno_filter_arg['measure']):
                continue
            pheno_constraints = self._get_pheno_filter_constraints(
                pheno_filter_arg)

            pheno_filter = self.pheno_filter_builder.make_filter(
                pheno_filter_arg['measure'], pheno_constraints)

            measure_df = self.phenotype_data.get_measure_values_df(
                pheno_filter_arg['measure'],
                roles=[pheno_filter_arg["role"]])

            measure_df = pheno_filter.apply(measure_df)

            people_ids.append(set(measure_df['person_id']))

        if not people_ids:
            return set()

        return functools.reduce(set.intersection, people_ids)

    def _transform_pheno_filter(self, kwargs):
        pheno_filter_args = kwargs.pop('phenoFilters')

        assert isinstance(pheno_filter_args, list)
        assert self.phenotype_data

        people_ids_to_query = self._transform_pheno_filters_to_people_ids(
            pheno_filter_args)
        people_ids_to_query = self._merge_with_people_ids(
            kwargs, people_ids_to_query)

        if len(people_ids_to_query) == 0:
            return None
        assert not kwargs.get('person_ids'), \
            "Rethink how to combine person ids"
        kwargs['person_ids'] = people_ids_to_query

        return kwargs

    def _add_roles_to_query(self, roles_query, kwargs):
        if not roles_query:
            return

        roles_query = OrNode(roles_query)

        original_roles = kwargs.get('roles', None)
        if original_roles is not None:
            if isinstance(original_roles, str):
                original_roles = role_query.transform_query_string_to_tree(
                    original_roles)
            kwargs['roles'] = AndNode([original_roles, roles_query])
        else:
            kwargs['roles'] = roles_query

    def _get_legend_default_values(self):
        return [{
            'color': '#E0E0E0',
            'id': 'missing-person',
            'name': 'missing-person'
        }]

    def get_legend(self, *args, **kwargs):
        if 'peopleGroup' not in kwargs:
            legend = list(self.legend.values())[0] if self.legend else []
        else:
            legend = self.legend.get(kwargs['peopleGroup']['id'], [])

        return legend + self._get_legend_default_values()

    def get_present_in_role(self, present_in_role_id):
        if not present_in_role_id:
            return {}

        present_in_role = list(filter(
            lambda present_in_role: present_in_role.section_id() ==
            present_in_role_id, self.present_in_role))

        return present_in_role[0] if present_in_role else {}

    def get_genotype_data_group_description(self):
        keys = [
            'id', 'name', 'description', 'phenotype_browser', 'phenotype_tool',
            'phenotype_data', 'people_group', 'common_report', 'study_type',
            'studies', 'has_present_in_child', 'has_present_in_parent'
        ]
        # TODO Add domain to pheno filters
        result = {key: deepcopy(getattr(self.config, key, None)) for key in keys}


        bs_config = GPFConfigParser._namedtuple_to_dict(deepcopy(self.config.genotype_browser))
        bs_config["columns"] = bs_config["genotype"]

        result['genotype_browser_config'] = bs_config
        result['genotype_browser'] = self.config.genotype_browser.enabled or False

        result['study_types'] = result['study_type']
        result['enrichment_tool'] = self.config.enrichment.enabled
        result['common_report'] = GPFConfigParser._namedtuple_to_dict(result['common_report'])
        result['people_group'] = GPFConfigParser._namedtuple_to_dict(result['people_group'])

        result['name'] = result['name'] or result['id']

        return result

    def _get_wdae_member(self, member, people_group, best_st):
        return [
            member.family_id,
            member.person_id,
            member.mom_id if member.mom_id else '0',
            member.dad_id if member.dad_id else '0',
            member.sex.short(),
            str(member.role),
            self.genotype_data_study._get_person_color(member, people_group),
            member.layout,
            member.generated,
            best_st,
            0
        ]
