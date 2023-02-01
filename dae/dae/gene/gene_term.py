#!/bin/env python
# pylint: disable=invalid-name

from collections import defaultdict


def dd():
    return defaultdict(int)


class GeneTerms:
    """Class representing gene terms."""

    def __init__(self):
        self.g2T = defaultdict(dd)
        self.t2G = defaultdict(dd)
        self.tDesc = {}
        self.geneNS = None

    def filterGenes(self, filterF):
        """Filter the genese."""
        keepGs = filterF(list(self.g2T.keys()))
        self.g2T = {g: ts for g, ts in list(self.g2T.items()) if g in keepGs}
        self.t2G = defaultdict(dd)
        for g, ts in list(self.g2T.items()):
            for t, n in list(ts.items()):
                self.t2G[t][g] = n
        for t in set(self.tDesc) - set(self.t2G):
            del self.tDesc[t]

    def renameGenes(self, geneNS, renameF):
        """Rename genese."""
        g2T = self.g2T
        self.g2T = defaultdict(dd)
        self.t2G = defaultdict(dd)
        for g, ts in list(g2T.items()):
            ng = renameF(g)
            if ng:
                self.g2T[ng] = ts
        for g, ts in list(self.g2T.items()):
            for t, n in list(ts.items()):
                self.t2G[t][g] = n
        for t in set(self.tDesc) - set(self.t2G):
            del self.tDesc[t]
        self.geneNS = geneNS

    def save(self, fn):
        """Save to `fn`."""
        if fn.endswith("-map.txt"):
            mapFn = fn
            dscFn = fn[:-4] + "names.txt"
        else:
            mapFn = fn + "-map.txt"
            dscFn = fn + "-mapnames.txt"

        with open(mapFn, "w") as mapF:
            mapF.write("#geneNS\t" + self.geneNS + "\n")
            for g in sorted(self.g2T):
                ts = []
                for t, tn in sorted(self.g2T[g].items()):
                    ts += [t] * tn
                mapF.write(g + "\t" + " ".join(ts) + "\n")

        with open(dscFn, "w") as dscFn:
            dscFn.write(
                "\n".join(
                    [t + "\t" + dsc for t, dsc in sorted(self.tDesc.items())]
                )
                + "\n"
            )


def read_ewa_set_file(set_files):
    """Read a set of ewa files."""
    r = GeneTerms()
    r.geneNS = "sym"
    for f in set_files:
        setname = f.readline().strip()
        line = f.readline()
        r.tDesc[setname] = line.strip()
        for line in f:
            gene_sym = line.strip()
            r.t2G[setname][gene_sym] += 1
            r.g2T[gene_sym][setname] += 1
        f.close()
    return r


def read_gmt_file(input_file):
    """Read a gmt file."""
    r = GeneTerms()
    r.geneNS = "sym"

    for ln in input_file:
        line = ln.strip().split()

        t = line[0]
        r.tDesc[t] = line[1]
        for gs in line[2:]:
            r.t2G[t][gs] += 1
            r.g2T[gs][t] += 1
    input_file.close()
    return r


def read_mapping_file(input_file, names_file):
    """Read a mapping file."""
    r = GeneTerms()
    r.geneNS = "id"
    for ln in input_file:
        line = ln.strip().split()
        if line[0] == "#geneNS":
            r.geneNS = line[1]
            continue
        geneId = line[0]
        del line[0]
        for t in line:
            r.t2G[t][geneId] += 1
            r.g2T[geneId][t] += 1
    input_file.close()
    if names_file is not None:
        try:
            for line in names_file:
                (t, desc) = line.strip().split("\t", 1)
                if t in r.t2G:
                    r.tDesc[t] = desc
        except IOError:
            pass
        names_file.close()
    for t in set(r.t2G) - set(r.tDesc):
        r.tDesc[t] = ""
    return r
