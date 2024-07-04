import pathlib
from collections import defaultdict
from typing import IO, Any, Callable


def dd() -> dict[str, int]:
    return defaultdict(int)


class GeneTerms:
    """Class representing gene terms."""

    def __init__(self) -> None:
        self.g2t: dict[str, Any] = defaultdict(dd)
        self.t2g: dict[str, Any] = defaultdict(dd)
        self.t_desc: dict[str, Any] = {}
        self.gene_ns: str | None = None

    def filter_genes(
        self, filter_fun: Callable[[list[str]], list[str]],
    ) -> None:
        """Filter the genes."""
        keep_gs = filter_fun(list(self.g2t.keys()))
        self.g2t = {g: ts for g, ts in list(self.g2t.items()) if g in keep_gs}
        self.t2g = defaultdict(dd)
        for g, ts in list(self.g2t.items()):
            for t, n in list(ts.items()):
                self.t2g[t][g] = n
        for t in set(self.t_desc) - set(self.t2g):
            del self.t_desc[t]

    def rename_genes(
        self, gene_ns: str | None,
        rename_fun: Callable[[str], str],
    ) -> None:
        """Rename genese."""
        g2t = self.g2t
        self.g2t = defaultdict(dd)
        self.t2g = defaultdict(dd)
        for g, ts in list(g2t.items()):
            ng = rename_fun(g)
            if ng:
                self.g2t[ng] = ts
        for g, ts in list(self.g2t.items()):
            for t, n in list(ts.items()):
                self.t2g[t][g] = n
        for t in set(self.t_desc) - set(self.t2g):
            del self.t_desc[t]
        self.gene_ns = gene_ns

    def save(self, fname: str) -> None:
        """Save to `fn`."""
        if fname.endswith("-map.txt"):
            map_fname = fname
            dsc_fname = fname[:-4] + "names.txt"
        else:
            map_fname = fname + "-map.txt"
            dsc_fname = fname + "-mapnames.txt"

        with open(map_fname, "wt") as outfile:
            outfile.write("#geneNS\t" + str(self.gene_ns) + "\n")
            for g in sorted(self.g2t):
                ts = []
                for t, tn in sorted(self.g2t[g].items()):
                    ts += [t] * tn
                outfile.write(g + "\t" + " ".join(ts) + "\n")

        pathlib.Path(dsc_fname).write_text(
                "\n".join(
                    [t + "\t" + dsc for t, dsc in sorted(self.t_desc.items())],
                )
                + "\n",
        )


def read_ewa_set_file(set_files: list[IO]) -> GeneTerms:
    """Read a set of ewa files."""
    r = GeneTerms()
    r.gene_ns = "sym"
    for f in set_files:
        setname = ""
        while setname == "":
            setname = f.readline().strip()
        line = f.readline()
        r.t_desc[setname] = line.strip()
        for line in f:
            gene_sym = line.strip()
            r.t2g[setname][gene_sym] += 1
            r.g2t[gene_sym][setname] += 1
        f.close()
    return r


def read_gmt_file(input_file: IO) -> GeneTerms:
    """Read a gmt file."""
    r = GeneTerms()
    r.gene_ns = "sym"

    for ln in input_file:
        line = ln.strip().split()

        t = line[0]
        r.t_desc[t] = line[1]
        for gs in line[2:]:
            r.t2g[t][gs] += 1
            r.g2t[gs][t] += 1
    input_file.close()
    return r


def read_mapping_file(input_file: IO, names_file: IO | None) -> GeneTerms:
    """Read a mapping file."""
    r = GeneTerms()
    r.gene_ns = "id"
    for ln in input_file:
        line = ln.strip().split()
        if line[0] == "#geneNS":
            r.gene_ns = line[1]
            continue
        gene_id = line[0]
        del line[0]
        for t in line:
            r.t2g[t][gene_id] += 1
            r.g2t[gene_id][t] += 1
    input_file.close()
    if names_file is not None:
        try:
            for line in names_file:
                (t, desc) = line.strip().split("\t", 1)
                if t in r.t2g:
                    r.t_desc[t] = desc
        except OSError:
            pass
        names_file.close()
    for t in set(r.t2g) - set(r.t_desc):
        r.t_desc[t] = ""
    return r
