"""
Expected result should be similar to:
-------------------------------------

STUDIES: IossifovWE2012
FAMILIES: 343
        By number of children: 2: 343
        314 male and 29 female probands.
        161 male and 182 female siblings.
        prbMsibF: 167, prbMsibM: 147, prbFsibF: 15, prbFsibM: 14
+++++++++++++++++++++++++++++++++++++++++++
effect                  prb                     sib                     prbM                    prbF                    sibM                    sibF
------------------------------------------
LGDs         	 59,0.172 ( 57,16.6%) 	 30,0.087 ( 28, 8.2%) 	 50,0.159 ( 48,15.3%) 	  9,0.310 (  9,31.0%) 	 17,0.106 ( 16, 9.9%) 	 13,0.071 ( 12, 6.6%)
frame-shift  	 31,0.090 ( 31, 9.0%) 	 15,0.044 ( 14, 4.1%) 	 26,0.083 ( 26, 8.3%) 	  5,0.172 (  5,17.2%) 	 11,0.068 ( 11, 6.8%) 	  4,0.022 (  3, 1.6%)
nonsense     	 21,0.061 ( 21, 6.1%) 	 11,0.032 ( 11, 3.2%) 	 18,0.057 ( 18, 5.7%) 	  3,0.103 (  3,10.3%) 	  4,0.025 (  4, 2.5%) 	  7,0.038 (  7, 3.8%)
splice-site  	  7,0.020 (  7, 2.0%) 	  3,0.009 (  3, 0.9%) 	  6,0.019 (  6, 1.9%) 	  1,0.034 (  1, 3.4%) 	  2,0.012 (  2, 1.2%) 	  1,0.005 (  1, 0.5%)
missense     	206,0.601 (151,44.0%) 	203,0.592 (154,44.9%) 	187,0.596 (136,43.3%) 	 19,0.655 ( 15,51.7%) 	 90,0.559 ( 70,43.5%) 	113,0.621 ( 84,46.2%)
synonymous   	 88,0.257 ( 77,22.4%) 	 77,0.224 ( 68,19.8%) 	 80,0.255 ( 71,22.6%) 	  8,0.276 (  6,20.7%) 	 30,0.186 ( 27,16.8%) 	 47,0.258 ( 41,22.5%)
CNVs         	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%)
CNV+         	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%)
CNV-         	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%)
noStart      	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%)
noEnd        	  1,0.003 (  1, 0.3%) 	  0,0.000 (  0, 0.0%) 	  1,0.003 (  1, 0.3%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%)
5'UTR        	  7,0.020 (  7, 2.0%) 	  4,0.012 (  4, 1.2%) 	  5,0.016 (  5, 1.6%) 	  2,0.069 (  2, 6.9%) 	  2,0.012 (  2, 1.2%) 	  2,0.011 (  2, 1.1%)
3'UTR        	  9,0.026 (  9, 2.6%) 	  3,0.009 (  3, 0.9%) 	  9,0.029 (  9, 2.9%) 	  0,0.000 (  0, 0.0%) 	  2,0.012 (  2, 1.2%) 	  1,0.005 (  1, 0.5%)
3'UTR-intron 	  1,0.003 (  1, 0.3%) 	  0,0.000 (  0, 0.0%) 	  1,0.003 (  1, 0.3%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%) 	  0,0.000 (  0, 0.0%)
5'UTR-intron 	  5,0.015 (  5, 1.5%) 	  3,0.009 (  3, 0.9%) 	  5,0.016 (  5, 1.6%) 	  0,0.000 (  0, 0.0%) 	  2,0.012 (  2, 1.2%) 	  1,0.005 (  1, 0.5%)
intron       	 90,0.262 ( 86,25.1%) 	 97,0.283 ( 80,23.3%) 	 83,0.264 ( 79,25.2%) 	  7,0.241 (  7,24.1%) 	 47,0.292 ( 41,25.5%) 	 50,0.275 ( 39,21.4%)
non-coding-intron 	 15,0.044 ( 15, 4.4%) 	 13,0.038 ( 12, 3.5%) 	 14,0.045 ( 14, 4.5%) 	  1,0.034 (  1, 3.4%) 	  5,0.031 (  4, 2.5%) 	  8,0.044 (  8, 4.4%)
non-coding   	 28,0.082 ( 27, 7.9%) 	 25,0.073 ( 23, 6.7%) 	 25,0.080 ( 24, 7.6%) 	  3,0.103 (  3,10.3%) 	 12,0.075 ( 10, 6.2%) 	 13,0.071 ( 13, 7.1%)
------------------------------------------
LGDs RATES:
        Probands: all: 0.172, M: 0.159, F: 0.310 (MvsF p-val: 0.094)
        Siblings: all: 0.087, M: 0.106, F: 0.071 (MvsF p-val: 0.361)
missense RATES:
        Probands: all: 0.601, M: 0.596, F: 0.655 (MvsF p-val: 0.706)
        Siblings: all: 0.592, M: 0.559, F: 0.621 (MvsF p-val: 0.482)
CNVs RATES:
        Probands: all: 0.000, M: 0.000, F: 0.000 (MvsF p-val: 1.000)
        Siblings: all: 0.000, M: 0.000, F: 0.000 (MvsF p-val: 1.000)

"""

from dae_query import get_child_types
from DAE import vDB
from collections import defaultdict
from collections import Counter
import scipy.stats as stats


def effect_types():
    return ['LGDs',
            'frame-shift',
            'nonsense',
            'splice-site',
            'missense',
            'synonymous',
            'CNVs',
            'CNV+',
            'CNV-',
            'noStart',
            'noEnd',
            "5'UTR",
            "3'UTR",
            "3'UTR-intron",
            "5'UTR-intron",
            "intron",
            "non-coding-intron",
            "non-coding"]


def effect_type_sets():
    eff_types_sa = effect_types()
    return [vDB.effectTypesSet(eft) for eft in eff_types_sa]


def effect_indices():
    indices = defaultdict(list)
    for i, eft_set in enumerate(effect_type_sets()):
        for eff in eft_set:
            indices[eff].append(i)
    return indices


def family_buffer(studies):
    fam_buff = defaultdict(dict)
    for study in studies:
        for f in study.families.values():
            for p in [f.memberInOrder[c] for c in xrange(2, len(f.memberInOrder))]:
                if p.personId in fam_buff[f.familyId]:
                    prev_p = fam_buff[f.familyId][p.personId]
                    if prev_p.role != p.role or prev_p.gender != p.gender:
                        raise Exception("Person role/gender mismatch")
                else:
                    fam_buff[f.familyId][p.personId] = p
    return fam_buff


def __format_header_summary(fam_total, child_cnt_hist,
                            child_type_cnt, fam_type_cnt):
    """
print "FAMILIES:", len(famBuff)
print "\tBy number of children: " + ", ".join([str(nc) + ": " +
    str(chldNHist[nc]) for nc in sorted(chldNHist.keys())])
print "\t" + str(chldTpCnt['prbM']), "male and",
    str(chldTpCnt['prbF']), "female probands."
print "\t" + str(chldTpCnt['sibM']), "male and",
    str(chldTpCnt['sibF']), "female siblings."
print "\t" +  ", ".join([x[0] + ": " + str(x[1])
    for x in sorted(fmTpCnt.items(),key=lambda x: -x[1])])
print "+++++++++++++++++++++++++++++++++++++++++++"
    """

    number_of_children = [str(nc)+": " + str(child_cnt_hist[nc])
                          for nc in sorted(child_cnt_hist.keys())]

    family_types = [ft[0] + ": " + str(ft[1])
                    for ft in sorted(fam_type_cnt.items(),
                                     key=lambda ft: -ft[1])]
    return {"fam_total": str(fam_total),
            "number_of_children": number_of_children,
            "probants": [str(child_type_cnt['prbM']), str(child_type_cnt['prbF'])],
            "siblings": [str(child_type_cnt['sibM']), str(child_type_cnt['sibF'])],
            'family_type': family_types}


def build_header_summary(studies):
    child_cnt_hist = Counter()
    fam_type_cnt = Counter()
    child_type_cnt = Counter()

    fam_buff = family_buffer(studies)
    for fmd in fam_buff.values():
        child_cnt_hist[len(fmd)] += 1

        fam_conf = "".join([fmd[pid].role + fmd[pid].gender
                            for pid in sorted(fmd.keys(),
                                              key=lambda x: (fmd[x].role, x))])
        fam_type_cnt[fam_conf] += 1
        for p in fmd.values():
            child_type_cnt[p.role + p.gender] += 1
            child_type_cnt[p.role] += 1

    fam_total = len(fam_buff)

    return [fam_total, child_cnt_hist, child_type_cnt, fam_type_cnt]


def ratio_str(x, n):
    if n == 0:
        return " NA  "
    return "%.3f" % (float(x)/float(n))


def prcnt_str(x, n):
    if n == 0:
        return " NA  "
    return "%4.1f%%" % (100.0 * float(x) / n)


def bnm_tst(xM, xF, NM, NF):
        if NM + NF == 0:
            return " NA  "
        return "%.3f" % (stats.binom_test(xF, xF+xM, p=float(NF)/(NM+NF)))


def filter_vs(vs):
    ret = []
    seen = set()
    for v in vs:
        hasNew = False
        for ge in v.requestedGeneEffects:
            sym = ge['sym']
            kk = v.familyId + "." + sym
            if kk not in seen:
                hasNew = True
            seen.add(kk)
        if hasNew:
            ret.append(v)
    return ret


def __format_variants(vs_cnt, child_type_cnt):
    return "%3d, %s" % \
        (vs_cnt,
         ratio_str(vs_cnt,
                   child_type_cnt))


def __format_child_types(ch_cnt, child_type_cnt):
    return "%3d, %s" % \
        (ch_cnt,
         prcnt_str(ch_cnt,
                   child_type_cnt))


def build_stats(studies):
    header = build_header_summary(studies)
    [total, child_cnt_hist, child_type_cnt, fam_cnt] = header

    stats = defaultdict(list)
    stats['children'] = get_child_types()

    cnts = defaultdict(lambda: defaultdict(float))

    for effect_type in effect_types():
        for child in get_child_types():
            vs = list(vDB.get_denovo_variants(studies,
                                              inChild=child,
                                              effectTypes=effect_type))
            vs = filter_vs(vs)

            vs_cnt = len(vs)
            ch_cnt = len(set(v.familyId for v in vs))

            data = [__format_variants(vs_cnt,
                                      child_type_cnt[child]),
                    __format_child_types(ch_cnt,
                                         child_type_cnt[child])]
            stats[effect_type].append(data)
            cnts[child][effect_type] = vs_cnt

    footer = defaultdict(list)
    footer['order'] = ['LGDs', 'missense', 'CNVs']
    for effect_type in footer['order']:
        probants = [ratio_str(cnts['prb'][effect_type], child_type_cnt['prb']),
                    ratio_str(cnts['prbM'][effect_type], child_type_cnt['prbM']),
                    ratio_str(cnts['prbF'][effect_type], child_type_cnt['prbF']),
                    bnm_tst(cnts['prbM'][effect_type],
                            cnts['prbF'][effect_type],
                            child_type_cnt['prbM'],
                            child_type_cnt['prbF'])]
        siblings = [ratio_str(cnts['sib'][effect_type], child_type_cnt['sib']),
                    ratio_str(cnts['sibM'][effect_type], child_type_cnt['sibM']),
                    ratio_str(cnts['sibF'][effect_type], child_type_cnt['sibF']),
                    bnm_tst(cnts['sibM'][effect_type],
                            cnts['sibF'][effect_type],
                            child_type_cnt['sibM'],
                            child_type_cnt['sibF'])]

        footer[effect_type].append([probants, siblings])

    return {'header': __format_header_summary(*header),
            'result': dict(stats),
            'footer': dict(footer),
            'rows': effect_types(),
            'cols': get_child_types()}
