import itertools
import functools

DEFAULT_COLUMN_TITLES = {
    'familyId': 'family id',
    'location': 'location',
    'variant': 'variant',
    'bestSt': 'family genotype',
    'fromParentS': 'from parent',
    'inChS': 'in child',
    'effectType': 'worst effect type',
    'worstEffect': 'worst requested effect',
    'genes': 'genes',
    'geneEffect': 'all effects',
    'requestedGeneEffects': 'requested effects',
    'popType': 'population type',
    'effectDetails': 'effect details',
    'all.altFreq': 'alternative allele frequency',
    'all.nAltAlls': 'number of alternative alleles',
    'all.nParCalled': 'number of genotyped parents',
    '_par_races_': 'parent races',
    '_ch_prof_': 'children description',
    '_prb_viq_': 'proband verbal iq',
    '_prb_nviq_': 'proband non-verbal iq',
    'studyName': 'study',
    '_phenotype_': 'study phenotype',
    'counts': 'count',
    'valstatus': 'validation status',
    '_pedigree_': '_pedigree_',
    'phenoInChs': 'phenoInChs',
    'dataset': 'dataset',
    'SSCfreq': 'SSCfreq',
    'EVSfreq': 'EVSfreq',
    'E65freq': 'E65freq',
}


def merge_dicts(*dicts):
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


def ge2str(gs):
    return "|".join(g.symbol + ":" + g.effect for x in gs for g in x.gene)


def mat2str(mat, col_sep=" ", row_sep="/"):
    return row_sep.join([col_sep.join([str(n) for n in mat[i, :]])
                        for i in xrange(mat.shape[0])])


def gene_effect_get_worst_effect(gs):
    if len(gs) == 0:
        return ''
    return gs[0]['eff']


def gene_effect_get_genes(gs):
    if len(gs) == 0:
        return ''
    # genes_set = set([g['sym'] for g in gs if g['eff'] == gs[0]['eff']])
    genes_set = set([g['sym'] for g in gs])
    genes = list(genes_set)

    return ';'.join(genes)


STANDARD_ATTRS = {
    "family": "family_id",
    "location": "location",
    "vcf": "vcf",
}


def get_standard_attr(key, v):
    return getattr(v, STANDARD_ATTRS[key])


STANDARD_ATTRS_LAMBDAS = {
    key: functools.partial(get_standard_attr, key)
    for key, val in STANDARD_ATTRS.items()
}

SPECIAL_ATTRS_FORMAT = {
    "bestSt": lambda v: mat2str(getattr(v, "bestSt")),
    "counts": lambda v: mat2str(getattr(v, "counts")),
    "genotype": lambda v: mat2str(getattr(v, "genotype")),
    "effect": lambda v: ge2str(getattr(v, "effect")),
    "requestedGeneEffects": lambda v:
        ge2str(getattr(v, "requestedGeneEffects")),
}

SPECIAL_GENE_EFFECTS = {
    "genes": lambda v: gene_effect_get_genes(getattr(v, "genes")),
    "worstEffect": lambda v: gene_effect_get_worst_effect(getattr(v, "genes"))
}


SPECIAL_ATTRS = merge_dicts(
    SPECIAL_ATTRS_FORMAT,
    SPECIAL_GENE_EFFECTS,
    STANDARD_ATTRS_LAMBDAS
)


def transform_variants_to_lists(variants, attrs):
    for v in variants:
        row_variant = []
        for attr in attrs:
            try:
                if attr in SPECIAL_ATTRS:
                    row_variant.append(SPECIAL_ATTRS[attr](v))
                else:
                    row_variant.append(str(getattr(v, attr, '')))
            except (AttributeError, KeyError) as e:
                print(attr, type(e), e)
                row_variant.append('')
        yield row_variant


def get_variants_web_preview(
        variants, attrs, max_variants_count=1000):
    VARIANTS_HARD_MAX = 2000
    rows = transform_variants_to_lists(variants, attrs)
    count = min(max_variants_count, VARIANTS_HARD_MAX)

    limited_rows = itertools.islice(rows, count)

    if count <= max_variants_count:
        count = str(count)
    else:
        count = 'more than {}'.format(max_variants_count)

    return {
        'count': count,
        'cols': attrs,
        'rows': list(limited_rows)
    }
