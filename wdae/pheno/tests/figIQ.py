#!/bin/env python

from pylab import *
from scipy.stats import ttest_ind, norm, ks_2samp
from DAE import *
from itertools import groupby
from numpy.lib.npyio import genfromtxt
from collections import defaultdict


# infile = '/data/safe/levy/review/forMikeAndKenny-20130523.txt'
# infile = 'forMikeAndKenny-20130523.txt'
infile = 'phnGnt.csv'

# familySet = 'SendWE'
# familySet = 'WE'
# familySet = 'PublishedWE'
familySet = ''


dt = genfromtxt(
    infile, delimiter='\t', dtype=None, names=True, case_sensitive=True)
print(dt)

maleNvIQs = [float(dtr['nvIQ']) for dtr in dt if dtr[
    'probandGender'] == 'male' and dtr['nvIQ'] != "NA"]
femaleNvIQs = [float(dtr['nvIQ']) for dtr in dt if dtr[
    'probandGender'] == 'female' and dtr['nvIQ'] != "NA"]


# grD = r_[c_[ maleNvIQs,   ones( (len( maleNvIQs ),1))],
#         c_[femaleNvIQs, zeros((len(femaleNvIQs),1))]  ]
# grD = grD[grD[:,0].argsort(),:]
# maleTimes = grD[:,1].cumsum() / (arange(len(grD))+1-grD[:,1].cumsum())

'''
twinx()
plot(grD[:,0],maleTimes,'k',lw=3)
ylim([0,10])
ylabel('male excess', fontsize=15)
grid(True,axis='y')
'''
# gcf().savefig('IQ-A.pdf')


# show()
# import sys
# sys.exit(0)

def pMS(column, gender, has, xloc,
        marker="o", lw=2, ms=10, mfc='white', addLabel=False):
    if gender == "male":
        color = "blue"
    else:
        color = 'red'
    if has:
        mfc = color
    else:
        mfc = 'white'

    if column is None:
        raise Exception("should not be here!!")
        # data = [float(dtr['nvIQ']) for dtr in dt if dtr['LGDs'+familySet]!='NA' and dtr['probandGender']==gender and dtr['nvIQ']!="NA"]
    else:
        if has:
            data = [float(dtr['nvIQ']) for dtr in dt
                    if dtr[column] != 0 and dtr['nvIQ'] != "NA" and
                    dtr['probandGender'] == gender]
        else:
            data = [float(dtr['nvIQ']) for dtr in dt if dtr['nvIQ'] != "NA" and
                    dtr['probandGender'] == gender]
    mn = mean(data)
    st = 1.96 * std(data) / sqrt(len(data))
    plot([xloc, xloc], [mn - st, mn + st], '_-', color=color,
         lw=lw, ms=ms, mfc=mfc, mew=2, mec=color)
    if addLabel:
        if has:
            label = gender + " with de novo type"
        else:
            label = gender + " without de novo type"
        plot([xloc], [mn], marker=marker, color=color, ms=ms,
             mfc=mfc, mew=2, mec=color, label=label, ls="")
    else:
        plot([xloc], [mn], marker=marker, color=color,
             ms=ms, mfc=mfc, mew=2, mec=color, ls="")
    return mn - st


def calcPV(column, gender):
    wt = [float(dtr['nvIQ']) for dtr in dt
          if dtr[column] != 0 and dtr['nvIQ'] != "NA" and
          dtr['probandGender'] == gender]
    wtout = [float(dtr['nvIQ']) for dtr in dt
             if dtr['nvIQ'] != "NA" and dtr['probandGender'] == gender]
    pV = ttest_ind(wt, wtout)[1]
    if pV >= 0.1:
        return "%.1f" % (pV)
    if pV >= 0.01:
        return "%.2f" % (pV)
    if pV >= 0.001:
        return "%.3f" % (pV)
    if pV >= 0.0001:
        return "%.3f" % (pV)
    return "%.5f" % (pV)


def pMS_block(column, start, label, small_gap=0.2, big_gap=0.4,
              addLabel=False, pval_offset=3):
    pvalue_male = calcPV(column, "male")
    pvalue_female = calcPV(column, "female")
    mx = np.inf
    fx = np.inf
    mx = min(
        mx, pMS(column, 'male', True, start + small_gap, addLabel=addLabel))
    mx = min(mx, pMS(column, 'male', False, start, addLabel=addLabel))
    fx = min(fx, pMS(
        column, 'female', True, start + 2 * small_gap + big_gap,
        addLabel=addLabel))
    fx = min(
        fx, pMS(column, 'female', False, start + small_gap + big_gap,
                addLabel=addLabel))
    print mx, fx
    if abs(mx - fx) < 5:
        mx = min(mx, fx)
        fx = mx
    text(start + small_gap + 0.5 * big_gap, texty,
         label, ha='center', fontsize=15, va='bottom')
    text(start + 0.5 * small_gap, mx - pval_offset, "%s" %
         pvalue_male, ha='center', fontsize=15, color='black')
    text(start + big_gap + 1.5 * small_gap, fx - pval_offset, "%s" %
         pvalue_female, ha='center', fontsize=15, color='black')
    return start + 2 * small_gap + big_gap

figure(figsize=(17, 17))
GSPC = GridSpec(2, 1, height_ratios=[5, 2])

'''
subplot(GSPC[0])

n,bins,patches = hist(maleNvIQs,25,normed=False,color='b')
n,bins,patches = hist(femaleNvIQs,bins,normed=False,color='r')
xlabel('non-verbal IQ', fontsize=15)
ylabel('number of probands', fontsize=15)
legend(['male','female'])
plot([90, 90], ylim(),'k--', lw=3)
XLM = xlim()
'''

# prbLGDs =  list(vDB.get_denovo_variants("combSSCWE,EichlerTG2012",inChild='prb', effectTypes="LGDs"))
prbLGDs = list(vDB.get_denovo_variants(
    "combSSCWE", inChild='prb', effectTypes="LGDs"))
# prbLGDs =  list(vDB.get_denovo_variants("allPublishedWEWithOurCallsAndTG",inChild='prb', effectTypes="LGDs"))

gnSorted = sorted([[ge['sym'], v.familyId, v.location, v]
                   for v in prbLGDs for ge in v.requestedGeneEffects])
sym2Vars = {sym: [t[3] for t in tpi]
            for sym, tpi in groupby(gnSorted, key=lambda x: x[0])}
# sym2Fs = { sym: set([v.familyId for v in vs]) for sym, vs in sym2Vars.items() }
# recSym2Fs = {a:b for a,b in sym2Fs.items() if len(b) > 1}

recSym2Fs = defaultdict(dict)
for gn, vs in sym2Vars.items():
    fmVars = defaultdict(set)
    for v in vs:
        fmVars[v.familyId].add(v)
    if len(fmVars) < 2:
        continue
    for fmId, fvs in fmVars.items():
        effs = {ge['eff'] for v in fvs for ge in v.requestedGeneEffects}
        if len(effs) != 1:
            raise Exception('lele male')

        eff, = effs
        recSym2Fs[gn][fmId] = eff

#####
# the categories string section
gts = get_gene_sets_symNS("main")

# genesWithLoFHitsInGirls = {ge['sym'] for v in vDB.get_denovo_variants(sscStudies, inChild='prbF', effectTypes="LGDs") for ge in v.requestedGeneEffects}
gsCodeDef = [
    # ("B", "brainExpressed",     "Brain expressed"),
    # ("G", genesWithLoFHitsInGirls,        "With LoF hits in girls"),
    ("F", gts.t2G["FMR1-targets"],       "FMRP targets"),
    ("C", gts.t2G["ChromatinModifiers"], "Chromatin modifiers"),
    ("E", gts.t2G["embryonic"],          "Embryonically expressed"),
    ("P", gts.t2G["PSD"],                "Postsynaptic density proteins"),
]
gsCodeSet = defaultdict(set)
for sCode, genesSet, sName in gsCodeDef:
    for gs in genesSet:
        gsCodeSet[gs].add(sCode)


def gsCode(g):
    return "".join([sCode if g in genesSet else "." for sCode, genesSet, sName in gsCodeDef])
##########################

subplot(GSPC[0])

maxIQ = max(maleNvIQs + femaleNvIQs)
bins = linspace(0, maxIQ, 25)
maxIQ = 180
H = 7
ymax = 300
bs = bins[1] - bins[0]
yyy = len(recSym2Fs) + 4
xs = bins[:-1]
ax = gca()


def drawGender(nvIQs, clr):

    hst = np.histogram(nvIQs, bins)[0]
    ys = hst * H / float(ymax)
    for bN in xrange(len(ys)):
        if ys[bN] > 0:
            ax.add_patch(
                Rectangle((xs[bN], yyy), bs, ys[bN], facecolor=clr, lw=1, edgecolor="k"))
            # ax.add_patch(Rectangle((xs[bN],yyy),bs,ys[bN],color="k",lw=1,edgecolor="k"))
            # ax.add_patch(Rectangle((xs[bN],yyy+ys[bN]),bs,0,color='k',lw=1))


drawGender(maleNvIQs, "b")
drawGender(femaleNvIQs, "r")

yy = len(recSym2Fs) + 1.5

AAA = 30

text(160 - AAA, yy, "Gene", horizontalalignment='center',
     verticalalignment='baseline', fontsize=20, fontweight="bold")
text(85, yy, "non-verbal IQ", horizontalalignment='right',
     verticalalignment='baseline', fontsize=20, fontweight="bold")

for tx in [20, 100, 160]:
    text(tx, yyy - 0.2, str(tx), horizontalalignment='center',
         verticalalignment='top', fontsize=13)
for tx in [90]:
    text(tx - 1, yyy - 0.2, str(tx), horizontalalignment='right',
         verticalalignment='top', fontsize=13)

plot([90, 90], [0, yyy + H], color="gray", linestyle='--', lw=3)

text(184 - AAA, yy, "Categories", horizontalalignment='center',
     verticalalignment='baseline', fontsize=20, fontweight="bold")
eee = 204
for rl in ["proband", "unaffected"]:
    text(eee + 7.5 - AAA, yy + 1.2, rl, horizontalalignment='center',
         verticalalignment='baseline', fontsize=20, fontweight="bold")
    for effA in "LGD", "MS":
        text(eee - AAA, yy, effA, horizontalalignment='center',
             verticalalignment='baseline', fontsize=20, fontweight="bold")
        eee += 13

yyl = yy - 0.3
plot([0, 220], [yyl, yyl], 'k')

for xl in [198, 224]:
    plot([xl - AAA, xl - AAA], [yyl - 0.5, yyl + 2], 'k')
for xl in [150, 170, 211, 237]:
    plot([xl - AAA, xl - AAA], [yyl - 0.5, yyl + 1], 'k')

yyd = yyy + 6
xxd = 160

text(xxd,  yyd + 1, "Categories", horizontalalignment="left",
     fontname="monospace", fontsize=17, verticalalignment="center", fontweight="bold")
for cs, gns, cdsc in gsCodeDef:
    text(xxd,  yyd, cs, horizontalalignment="center",
         fontname="monospace", fontsize=20, verticalalignment="center")
    text(xxd + 3, yyd, cdsc, horizontalalignment="left",
         fontsize=17, verticalalignment="center")
    yyd -= 1

yyd = yyy + 6
xxd = 5
text(xxd,  yyd + 1, "Effect", horizontalalignment="left", fontname="monospace",
     fontsize=17, verticalalignment="center", fontweight="bold")
for mrk, dsc in [("o", "frameshift"), ("d", "nonsense"), ("^", "splice site")]:
    # text(xxd,  yyd,cs,horizontalalignment="center",fontname="monospace",fontsize=17)
    plot(xxd,  yyd, color="gray", marker=mrk, alpha=0.7, ms=13)
    text(xxd + 3, yyd, dsc, horizontalalignment="left",
         fontsize=17, verticalalignment="center")
    yyd -= 1

yyd = yyy + 6
xxd = 40
text(xxd,  yyd + 1, "Gender", horizontalalignment="left", fontname="monospace",
     fontsize=17, verticalalignment="center", fontweight="bold")
for gcl, dsc in [("b", "male"), ("r", "female")]:
    ax.add_patch(
        Rectangle((xxd - 3, yyd - 0.3), 5, 0.6, facecolor=gcl, lw=1, edgecolor="k"))
    text(xxd + 3, yyd, dsc, horizontalalignment="left",
         fontsize=17, verticalalignment="center")
    yyd -= 1

msrName = 'nvIQ'
msr = {}
for pdtr in dt:
    try:
        msr[str(pdtr['familyId'])] = (
            float(pdtr[msrName]), pdtr['probandGender'])
    except:
        pass


def countsHits(vars):
    gnSorted = sorted([[ge['sym'], v]
                       for v in vars for ge in v.requestedGeneEffects])
    sym2Vars = {sym: [t[1] for t in tpi]
                for sym, tpi in groupby(gnSorted, key=lambda x: x[0])}
    sym2FN = {sym: len(set([v.familyId for v in vs]))
              for sym, vs in sym2Vars.items()}
    # return {sym:n for sym,n in sym2FN.items() if n>1}
    return sym2FN, sym2Vars

RLS = ["prb", "sib"]
EFFS = ["LGDs", "missense"]
dnvDt = {}


def loadDnvDt():
    for rl in RLS:
        dnvDt[rl] = {}
        for effT in EFFS:
            dnvCnts, dnvVars = countsHits(
                vDB.get_denovo_variants("combSSCWE", inChild=rl, effectTypes=effT))
            dnvDt[rl][effT] = dnvCnts
loadDnvDt()


def getDnvDt(rl, effT, g):
    try:
        return str(dnvDt[rl][effT][g])
    except:
        return ""


###############################

def aaaa(fms):
    vls = [msr[fm][0] for fm in fms if fm in msr]
    # ppp = 1.0
    # if len(vls)>1:
    #     ppp = ttest_1samp(vls,0)[1]
    ppp = ks_2samp(vls, [x[0] for x in msr.values()])[1]

    print ppp, vls
    return -ppp
i = 0
GNS = recSym2Fs.keys()
srtNmEff = "LGDs"
for gn in sorted(GNS, key=lambda x: (-dnvDt['prb'][srtNmEff][x] if x in dnvDt['prb'][srtNmEff] else 0, [1 if c == '.' else 0 for c in gsCode(x)], x), reverse=True):
    # for ii,(gn,fms) in enumerate(sorted(recSym2Fs.items(), key=lambda tt:
    # aaaa(tt[1]))):
    fms = recSym2Fs[gn]
    VLS = sorted([list(msr[fm]) + [eff]
                  for fm, eff in fms.items() if fm in msr])
    # spread
    print "VLS", VLS
    if len(VLS) != len(fms):
        print "MISSED IQ", gn, len(VLS), len(fms), "..."

    if len(VLS) < 2:
        print "SKIPPING", gn, len(VLS), "..."
        # continue
    touched = False
    minDelta = 1.0
    for j in xrange(len(VLS) - 1):
        if VLS[j + 1][0] - VLS[j][0] < minDelta:
            touched = True
            VLS[j + 1][0] += minDelta
    if touched:
        print "SPREAD VLS", VLS

    femaleVls = [x[0] for x in VLS if x[1] == "female"]
    maleVls = [x[0] for x in VLS if x[1] == "male"]
    vls = [x[0] for x in VLS]

    i += 1
    if not maleVls and not femaleVls:
        continue
    # print i, gn, fms, vls
    # print gn+ ":\t" , ",".join(fms), ",".join(map(str,vls))
    plot(vls, i * ones(len(vls)), "-", color="black")
    eff2marker = {"frame-shift": "o", "nonsense": "d", "splice-site": '^'}
    sex2Clr = {"male": "b", "female": "r"}
    # plot(femaleVls, i * ones(len(femaleVls)),'o',color="red",alpha=0.7,ms=15)
    for iq, sex, eff in VLS:
        plot([iq], [i], sex2Clr[sex] + eff2marker[eff], alpha=0.7, ms=13)

    text(157 - AAA, i, gn, horizontalalignment='left',
         verticalalignment='center', fontsize=15)

    for si, sm in enumerate(gsCode(gn)):
        text(180 - AAA + 3 * si, i, sm, horizontalalignment='center',
             verticalalignment='center', fontsize=20, fontname="monospace")

    ddd = 204
    for rl in RLS:
        for effT in EFFS:
            text(ddd - AAA, i, getDnvDt(rl, effT, gn),
                 horizontalalignment='center', verticalalignment='center', fontsize=20)
            ddd += 13

msrValues = [x[0] for x in msr.values()]
mn, mx = min(msrValues), max(msrValues)
# xlim((mn,mx))
xlim([0, 220])
xticks(range(20, 160, 20))
# gcf().set_size_inches(8,8)
xlabel('IQ')
yticks([])
gca().set_axis_off()

subplot(GSPC[1])
firstIndex = 2
index = firstIndex
group_gap = 1
texty = 90
index = pMS_block('LGDs' + familySet, index, "LGDs\nall") + group_gap
index = pMS_block('recLGDs' + familySet, index, "LGDs\nrecurrent") + group_gap
index = pMS_block('LGDsInFMR1P' + familySet, index, "LGDs\nin FXG") + group_gap

index = pMS_block(
    'LGDsInChrmMod' + familySet, index, "LGDs\nin CHM") + group_gap
index = pMS_block(
    'LGDsInEmbryonic' + familySet, index, "LGDs\nin EMB") + group_gap

index = pMS_block('missense' + familySet, index, "missense\nall") + group_gap
index = pMS_block(
    'recMissense' + familySet, index, "missense\nrecurrent") + group_gap
index = pMS_block(
    'synonymous' + familySet, index, "synonymous\nall", addLabel=True) + group_gap
axis([firstIndex - 1.5 * group_gap, index, 40, 100])
legend(loc="lower right", numpoints=1)
xticks([])
ylabel("non-verbal IQ", fontsize=15)
tight_layout()
gcf().savefig('IQ.pdf')
# show()
