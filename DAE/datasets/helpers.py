import itertools

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


def mat2str(mat, colSep=" ", rowSep="/"):
    return rowSep.join([colSep.join([str(n) for n in mat[i, :]])
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


SPECIAL_ATTRS_FORMAT = {
    "bestSt": mat2str,
    "counts": mat2str,
    "geneEffect": ge2str,
    "requestedGeneEffects": ge2str,
}

SPECIAL_GENE_EFFECTS = {
    "genes": gene_effect_get_genes,
    "worstEffect": gene_effect_get_worst_effect
}


def transform_variants_to_lists(variants, attrs, sep='\t'):
    for v in variants:
        row_variant = []
        for attr in attrs:
            try:
                if attr in SPECIAL_ATTRS_FORMAT:
                    row_variant.append(SPECIAL_ATTRS_FORMAT[attr](getattr(v, attr, '')))
                elif attr in SPECIAL_GENE_EFFECTS:
                    row_variant.append(SPECIAL_GENE_EFFECTS[attr](
                        getattr(v, 'requestedGeneEffects')))
                elif attr in v.atts:
                    val = v.atts[attr]
                    if not isinstance(val, list):
                        val = str(val).replace(sep, ';').replace("'", '"')
                    row_variant.append(val if val and val != 'False' and
                                val != 'None' else "")
                else:
                    row_variant.append(getattr(v, attr))
            except Exception:
                row_variant.append('')
        yield row_variant


def get_variants_web_preview(
        variants, attrs, sep='\t', max_variants_count=1000):
    VARIANTS_HARD_MAX = 2000
    rows = transform_variants_to_lists(variants, attrs, sep)
    count = min(max_variants_count, VARIANTS_HARD_MAX)

    limited_rows = itertools.islice(rows, count)

    if count <= max_variants_count:
        count = str(count)
    else:
        count = 'more than {}'.format(max_variants_count)

    return {
        'count': count,
        'cols': attrs,
        'rows': limited_rows
    }
