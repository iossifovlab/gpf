#!/usr/bin/env python

import optparse

import numpy as np
# from numpy import *
from scipy import stats
import numpy.random as rnd

from .vrtIOutil import ReaderStat, Writer, tooManyFile

from dae.gpf_instance.gpf_instance import GPFInstance


gpf_instance = GPFInstance()
genomes_db = gpf_instance.genomes_db


# family based data and mom and dad ordered state
# pp is even and num of people (count 2, mom and dad, per family)
# Alt count
# 0 1, and 2 copy state of an alternattive allele
# not handling Y chromosome
def xMF(xstr, pp):
    terms = xstr.split(';')	 # only families which have alternatives
    cnt = [[0, 0, 0], [0, 0, 0]]

    diplo_flag = [True, True]

    for x in terms:
        terms = x.split(':')
        bestStS = terms[1]
        z = [list(map(int, rs)) for rs in bestStS.split('/')]
        cnt[0][z[1][0]] += 1  # mom
        cnt[1][z[1][1]] += 1  # dad

        if(z[0][0] + z[1][0] < 2):
            diplo_flag[0] = False
        if(z[0][1] + z[1][1] < 2):
            diplo_flag[1] = False

    cnt[0][0] = pp / 2 - cnt[0][1] - cnt[0][2]
    cnt[1][0] = pp / 2 - cnt[1][1] - cnt[1][2]

    return cnt, diplo_flag


# ob : observed 2
# p : frequency
# s : population size and EVEN number (num of male and female are the same)
# smpl_size : sample size
def randomSampling(cnt, genF, smpl_size=10000, flagX=False):
    s = sum(cnt)
    eCnt = s * np.array(genF)

    T = sum([1.*(c-e)*(c-e)/e for c, e in zip(cnt, eCnt)])

    if flagX:
        p = (1.0 * cnt[1] + 2.0 * cnt[2]) / (1.5 * s)
        q = 1. - p

        v = rnd.multinomial(s / 2, [q*q, 2*p*q, p*p], size=smpl_size)
        w = rnd.multinomial(s / 2, [q, p, 0], size=smpl_size)

        x = v + w
    else:
        x = rnd.multinomial(s, genF, size=smpl_size)

    w = (x - eCnt)*(x - eCnt) / (1.*eCnt)
    n = sum(sum(w, 1) > T)

    pv = (1.0 * n) / smpl_size
    return pv


def G_test(cnt, eCnt):
    df = len(cnt) - 2

    T = sum([
        2. * c * np.log(c / e)
        for c, e in zip(cnt, eCnt) if c != 0
    ])
    pv = 1. - stats.chi2.cdf(sum(T), df)

    return pv


def Chi2_test(cnt, eCnt):
    df = len(cnt) - 2

    T = sum([(c-e)*(c-e)/e for c, e in zip(cnt, eCnt) if e != 0])
    pv = 1. - stats.chi2.cdf(sum(T), df)

    return pv


def Chi2_options(cnt, eCnt, genF, X=False):
    if np.sum(np.array(eCnt) < 5) < 1:
        return Chi2_test(cnt, eCnt)

    if (cnt[0] == 0 and eCnt[0] < 1) or (cnt[2] == 0 and eCnt[2] < 1):
        return 1.

    return randomSampling(cnt, genF, flagX=X)


# global variable
# defalult is False
# add -c to make it True
chi2_test_flag = True


def Test(cnt, eCnt, genF, X=False):
    global chi2_test_flag

    if chi2_test_flag:
        pv = Chi2_options(cnt, eCnt, genF, X)
    else:
        pv = G_test(cnt, eCnt)

    return pv


def pval_count_autosome(cnt):
    # cnt: [RR, RA, AA]
    N = sum(cnt)
    p = (1.0 * cnt[1] + 2.0 * cnt[2]) / (2.*N)

    genF = [(1-p)*(1-p), 2.*(1-p)*p, p*p]
    eCnt = [N*x for x in genF]

    pv = Test(cnt, eCnt, genF)

    return pv, eCnt


def pval_count_X(cnt):
    # cnt: [RR, RA, AA]
    # or   [R, A, '']
    N = sum(cnt)
    p = (1.0 * cnt[1] + 2.0 * cnt[2]) / (1.5 * N)

    genF = [
        (1-p) * (1-p) / 2.0 + (1-p) / 2.,
        (1-p)*p + p / 2.0, p * p / 2.
    ]
    eCnt = [N*x for x in genF]

    pv = Test(cnt, eCnt, genF, True)

    return pv, eCnt


par_x_test = genomes_db.get_pars_x_test()


def isPseudoAutosomalX(chrom, pos):
    global par_x_test
    return par_x_test(chrom, pos)


def Rx(xstr, pp, AXY, pos):
    xcnt, di_flag = xMF(xstr, pp)
    cnt = [xcnt[0][n] + xcnt[1][n] for n in range(len(xcnt[0]))]

    if (AXY == 'X') and (not isPseudoAutosomalX(AXY, pos)):
        pv, eCnt = pval_count_X(cnt)
    else:
        pv, eCnt = pval_count_autosome(cnt)

    return pv, cnt, eCnt


def main():
    usage = "usage: %prog options]"
    parser = optparse.OptionParser(usage=usage)

    parser.add_option(
        "-c", "--chisq", action="store_true", dest="chisq", default=False,
        metavar="chisq", help="chisq test, default [G-test]")

    ox, args = parser.parse_args()

    ref = ReaderStat(args[0])
    mny = ReaderStat(tooManyFile(args[0]))

    ref.notExistExit()

    global chi2_test_flag
    if not ox.chisq:
        chi2_test_flag = False

    gzW = Writer(args[1])
    gzW.write(ref.head + '\tHW\n')

    flag = True
    while flag:
        fi = ref.getFamilyData()
        if 'TOOMANY' == fi:
            if ref.cID == mny.cID:
                fi = mny.getFamilyData()
                mny.readLine()
            else:
                print('wrong', ref.cID, mny.cID)
                exit(1)

        cnt, pcnt = ref.getStat()

        terms = ref.cID.split(':')
        pv, cnt, eCnt = Rx(fi, cnt[0], terms[0], int(terms[1]))

        gzW.write(ref.cLine + '\t{0:.4f}'.format(pv) + '\n')

        flag = ref.readLine()


if __name__ == '__main__':
    main()
