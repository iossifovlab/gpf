#!/bin/env python

import numpy as np


def getDims(inp):
    return len(inp), inp[0].shape[1], sum(inp[0], 0)


def checkConsistency(inp):
    L, P, nCpies = getDims(inp)
    for locus, m in enumerate(inp):
        if m.shape != (2, P):
            raise Exception(
                "The matrix for the ", locus, "th locus has inconsisten shape"
            )

        lNC = sum(m, 0)
        if not np.array_equal(lNC, nCpies):
            raise Exception(
                "The ", locus, "th loci has inconsisten", "copynumber profile"
            )
    return True


def possiblePersonPhasingR(inp, L, P, p, ll, cPh, posPhs, seenHet):
    if ll == L:
        posPhs.append(cPh)
        return
    if inp[ll][0, p] == 0:
        cPh[:, ll] = 1
        possiblePersonPhasingR(inp, L, P, p, ll + 1, cPh, posPhs, seenHet)
    elif inp[ll][1, p] == 0:
        cPh[:, ll] = 0
        possiblePersonPhasingR(inp, L, P, p, ll + 1, cPh, posPhs, seenHet)
    elif seenHet:
        cPh[:, ll] = [0, 1]
        possiblePersonPhasingR(inp, L, P, p, ll + 1, cPh, posPhs, True)
        cPhB = np.array(cPh)
        cPhB[:, ll] = [1, 0]
        possiblePersonPhasingR(inp, L, P, p, ll + 1, cPhB, posPhs, True)
    else:
        cPh[:, ll] = [0, 1]
        possiblePersonPhasingR(inp, L, P, p, ll + 1, cPh, posPhs, True)


def possiblePersonPhasing(inp, L, P, nCpies, p):
    posPhs = []
    cPh = np.zeros((nCpies[p], L), dtype=int)
    possiblePersonPhasingR(inp, L, P, p, 0, cPh, posPhs, False)
    return posPhs


def phase(inp):
    L, P, nCpies = getDims(inp)
    # print >>sys.stderr, "inp:", inp
    # print >>sys.stderr, "L:", L
    # print >>sys.stderr, "P:", P
    # print >>sys.stderr, "nCpies:", nCpies
    # print >>sys.stderr, "phase called with L: %d, P, %d" % (L,P)

    chSts = set()

    for c in range(2, P):
        chSts.add(str(np.array([st[:, c] for st in inp])))

    posFamilyPhs = []
    for mph in possiblePersonPhasing(inp, L, P, nCpies, 0):
        for dph in possiblePersonPhasing(inp, L, P, nCpies, 1):
            posChSts = set()
            for mh in mph:
                for dh in dph:
                    m = np.zeros((L, 2), dtype=int)
                    for h in (mh, dh):
                        for locus in range(L):
                            m[locus, h[locus]] += 1
                    posChSts.add(str(m))
                if nCpies[1] == 1:
                    m = np.matrix(np.zeros((L, 2)))
                    for locus in range(L):
                        m[locus, mh[locus]] += 1
                    posChSts.add(str(m))
            print(chSts)
            print(posChSts)
            if all([x in posChSts for x in chSts]):
                posFamilyPhs.append((mph, dph))

    return posFamilyPhs


if __name__ == "__main__":
    print("hi")

    inpR = [
        [[1, 2, 2, 1], [1, 0, 0, 1]],
        [[1, 2, 1, 2], [1, 0, 1, 0]],
    ]
    inp = [np.array(x) for x in inpR]
    print("inp", inp)
    L, P, nCpies = getDims(inp)
    print("L:", L)
    print("P:", P)
    print("nCpies:", nCpies)

    posFamilyPhs = phase(inp)
    for pfphs in posFamilyPhs:
        print("-----------------")
        print("mom")
        print(pfphs[0])
        print("dad")
        print(pfphs[1])

    for ph in possiblePersonPhasing(inp, L, P, nCpies, 0):
        print("oo", ph)

    print(posFamilyPhs)

    L, P, nCpies = getDims(inp)
    print(L, P, nCpies)

    checkConsistency(inp)
    print("hurrey")

    for ph in possiblePersonPhasing(inp, L, P, nCpies, 1):
        print(ph)
