from __future__ import unicode_literals
from builtins import next
from builtins import str
import itertools
import logging
import helpers.GeneTerm
from django.http.request import QueryDict
from studies.helpers import mat2str

LOGGER = logging.getLogger(__name__)

# def load_gene_set(gene_set_label, study_name=None):
#     gene_term = gene_set_loader(gene_set_label, study_name)
#     gs = helpers.GeneTerm.GeneTerm(gene_term)
#     return gs

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


def ge2str(gs):
    return "|".join(x['sym'] + ":" + x['eff'] for x in gs)


SPECIAL_ATTRS_FORMAT = {
    "bestSt": mat2str,
    "counts": mat2str,
    "geneEffect": ge2str,
    "requestedGeneEffects": ge2str,
}


def __gene_effect_get_worst_effect(gs):
    if len(gs) == 0:
        return ''
    return gs[0]['eff']


def __gene_effect_get_genes(gs):
    if len(gs) == 0:
        return ''
    # genes_set = set([g['sym'] for g in gs if g['eff'] == gs[0]['eff']])
    genes_set = set([g['sym'] for g in gs])
    genes = list(genes_set)

    return ';'.join(genes)


SPECIAL_GENE_EFFECTS = {
    "genes": __gene_effect_get_genes,
    "worstEffect": __gene_effect_get_worst_effect
}


def generate_web_response(variants, attrs, sep='\t'):
    return {
        'cols': attrs,
        'rows': transform_variants_to_lists(variants, attrs, sep)
    }


def generate_response(
        variants, attrs=DEFAULT_COLUMN_TITLES.keys(),
        attr_labels=DEFAULT_COLUMN_TITLES, sep='\t'):
    variant_rows = transform_variants_to_lists(variants, attrs, sep)
    return itertools.chain([map(
        lambda attr: attr_labels.get(attr, attr), attrs)],
        variant_rows)


def transform_variants_to_lists(variants, attrs, sep='\t'):
    for v in variants:
        row_variant = []
        for attr in attrs:
            try:
                if attr in SPECIAL_ATTRS_FORMAT:
                    row_variant.append(SPECIAL_ATTRS_FORMAT[attr](
                        getattr(v, attr, '')))
                elif attr in SPECIAL_GENE_EFFECTS:
                    row_variant.append(SPECIAL_GENE_EFFECTS[attr](
                        getattr(v, 'requestedGeneEffects')))
                elif attr in v.atts:
                    val = v.atts[attr]
                    if not isinstance(val, list):
                        val = str(val).replace(sep, ';').replace("'", '"')
                    row_variant.append(
                        val if val and val != 'False' and
                        val != 'None' else "")
                else:
                    row_variant.append(getattr(v, attr))
            except Exception:
                row_variant.append('')
        yield row_variant


def join_line(l, sep='\t'):
    tl = map(lambda v: '' if v is None or v == 'None' else v, l)
    return sep.join(tl) + '\n'


def prepare_query_dict(data):
    res = []
    if isinstance(data, QueryDict):
        items = data.iterlists()
    else:
        items = list(data.items())

    for (key, val) in items:
        key = str(key)
        if isinstance(val, list):
            value = ','.join([str(s).strip() for s in val])
        elif isinstance(val, str) or isinstance(val, str):
            value = str(val.replace(u'\xa0', u' ').encode('utf-8'))
            value = value.strip()
        else:
            value = str(val)
        if value == '' or value.lower() == 'none':
            continue
        res.append((key, value))

    return dict(res)


def gene_terms_union(gene_terms):
    if len(gene_terms) == 1:
        return helpers.GeneTerm.GeneTerm(gene_terms[0])

    result = helpers.GeneTerm.GeneTerm(gene_terms[0])

    for gt in gene_terms[1:]:
        result.union(gt)

    return result


def collect_denovo_gene_sets(gene_set_phenotype):
    precomputed = register.get('denovo_gene_sets')
    denovo_gene_sets = precomputed.denovo_gene_sets
    if gene_set_phenotype is None:
        gene_set_phenotype = 'autism'
    phenotypes = gene_set_phenotype.split(',')
    gene_terms = [denovo_gene_sets[pheno] for pheno in phenotypes
                  if pheno in denovo_gene_sets]
    return gene_terms


def combine_denovo_gene_sets(gene_set_phenotype):
    gene_terms = collect_denovo_gene_sets(gene_set_phenotype)
    return gene_terms_union(gene_terms)


# def load_gene_set2(gene_set_label, gene_set_phenotype=None):
#     gene_term = None
#     if gene_set_label != 'denovo':
#         gene_term = get_gene_sets_symNS(gene_set_label)
#     else:
#         gene_term = combine_denovo_gene_sets(gene_set_phenotype)
#
#     if gene_term:
#         gs = helpers.GeneTerm.GeneTerm(gene_term)
#         return gs
#     return None


# def prepare_pheno_pedigree(cols, rows):
#     genotype_index = cols.index['family genotype']
#     from_parent_index = cols.index['from parent']
#     in_child_index = cols.index['in child']
#     population_type_index = cols.index['population type']
#     children_description_index=cols.index['children description']

#     for row in rows:
#         pass


def prepare_summary(vs):
    rows = []
    cols = next(vs)
    count = 0
    for r in vs:
        count += 1
        if count <= 1000:
            rows.append(r)
        if count > 2000:
            break

    if count <= 2000:
        count = str(count)
    else:
        count = 'more than 2000'

    return {'count': count,
            'rows': rows,
            'cols': cols}
