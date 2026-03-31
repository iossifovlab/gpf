import copy
import glob
import logging
import os
import pathlib
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import IO, Any, cast

logger = logging.getLogger(__name__)


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
        rename_fn: Callable[[str], str | None],
    ) -> None:
        """Rename genese."""
        g2t = self.g2t
        self.g2t = defaultdict(dd)
        self.t2g = defaultdict(dd)
        for g, ts in list(g2t.items()):
            ng = rename_fn(g)
            if ng:
                self.g2t[ng] = ts
        for g, ts in list(self.g2t.items()):
            for t, n in list(ts.items()):
                self.t2g[t][g] = n
        for t in set(self.t_desc) - set(self.t2g):
            del self.t_desc[t]
        self.gene_ns = gene_ns

    def save(self, fname: str) -> None:
        """Save to `fname`."""
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


@dataclass
class GeneInfo:
    gene_id: str
    gene_sym: str
    synonyms: set[str]
    description: str


def _add_gene_ns_token(
    ns_tokens: dict[str, dict[str, list[GeneInfo]]],
    ns: str,
    token: str,
    gi: GeneInfo,
) -> None:
    if ns not in ns_tokens:
        ns_tokens[ns] = {}
    tokens = ns_tokens[ns]
    if token not in tokens:
        tokens[token] = []
    tokens[token].append(gi)


def _parse_ncbi_gene_info(
    gene_info_file: str,
) -> tuple[dict[str, GeneInfo], dict[str, dict[str, list[GeneInfo]]]]:
    genes = {}
    ns_tokens: dict[str, dict[str, list[GeneInfo]]] = {}

    with open(gene_info_file) as f:
        for line in f:
            if line[0] == "#":
                # skipping comments
                continue
            cs = line.strip().split("\t")
            if len(cs) != 15:
                raise ValueError(
                    f"Unexpected line in the {gene_info_file}",
                )

            # Format: tax_id GeneID Symbol LocusTag Synonyms dbXrefs
            # chromosome map_location description
            # type_of_gene Symbol_from_nomenclature_authority
            # Full_name_from_nomenclature_authority Nomenclature_status
            # Other_designations Modification_date
            # (tab is used as a separator, pound sign - start of a comment)
            (
                _tax_id,
                gene_id,
                gene_sym,
                _locus_tag,
                synonyms,
                _db_xrefs,
                _chromosome,
                _map_location,
                description,
                _type_of_gene,
                _symbol_from_nomenclature_authority,
                _full_name_from_nomenclature_authority,
                _nomenclature_status,
                _other_designations,
                _modification_date,
            ) = cs

            gi = GeneInfo(
                gene_id=gene_id,
                gene_sym=gene_sym,
                synonyms=set(synonyms.split("|")) - {"-"},
                description=description,
            )

            if gi.gene_id in genes:
                raise ValueError(
                    f"The gene {gi.gene_id} is repeated in {gene_info_file}")

            genes[gi.gene_id] = gi
            _add_gene_ns_token(ns_tokens, "id", gi.gene_id, gi)
            _add_gene_ns_token(ns_tokens, "sym", gi.gene_sym, gi)
            for sym in gi.synonyms:
                _add_gene_ns_token(ns_tokens, "syns", sym, gi)

    return genes, ns_tokens


@dataclass
class NCBIGeneInfo:
    genes: dict[str, GeneInfo]
    ns_tokens: dict[str, dict[str, list[GeneInfo]]]


def load_ncbi_gene_info(gene_info_file: str) -> NCBIGeneInfo:
    genes, ns_tokens = _parse_ncbi_gene_info(gene_info_file)
    return NCBIGeneInfo(genes=genes, ns_tokens=ns_tokens)


def get_clean_gene_id(
    ncbi_gene_info: NCBIGeneInfo,
    ns: str,
    term: str,
) -> str | None:
    """Gene gene ID from NCBI gene info data."""
    ns_tokens = ncbi_gene_info.ns_tokens

    if ns not in ns_tokens:
        return None

    all_tokens = ns_tokens[ns]
    if term not in all_tokens:
        return None

    if len(all_tokens[term]) != 1:
        logger.info("multiple tokens for term %s in name space %s", term, ns)
        return None
    return all_tokens[term][0].gene_id


def rename_gene_terms(
    gene_terms: GeneTerms,
    gene_ns: str,
    ncbi_gene_info: NCBIGeneInfo,
) -> GeneTerms:
    """Rename gene terms using NCBI gene info data."""
    assert {gene_terms.gene_ns, gene_ns} <= {"id", "sym"}, (
        f"The provided namespaces {gene_terms.gene_ns}, "
        f"{gene_ns} must be either 'id' or 'sym'"
    )

    result = copy.deepcopy(gene_terms)

    if result.gene_ns == gene_ns:
        return result

    if result.gene_ns == "id" and gene_ns == "sym":

        def rename_fn(x: str) -> str | None:
            genes = ncbi_gene_info.genes
            if x in genes:
                return genes[x].gene_sym
            return None

        result.rename_genes("sym", rename_fn)
        return result

    if result.gene_ns == "sym" and gene_ns == "id":
        result.rename_genes(
            "id", lambda x: get_clean_gene_id(ncbi_gene_info, "sym", x),
        )
    return result


def load_gene_terms(path: str) -> GeneTerms | None:
    """Load gene terms from a file."""
    if path.endswith("-map.txt"):
        names_file = path[:-4] + "names.txt"
        if not pathlib.Path(names_file).exists():
            with open(path) as mapfile:
                return read_mapping_file(mapfile, None)
        else:
            with open(path) as mapfile, open(names_file) as namesfile:
                return read_mapping_file(mapfile, namesfile)
    if path.endswith(".gmt"):
        with open(path) as gmtfile:
            return read_gmt_file(gmtfile)

    # pylint: disable=consider-using-with
    infiles = [
        cast(IO, open(f, "rt"))  # noqa: SIM115
        for f in glob.glob(os.path.join(path, "*.txt"))
    ]
    return read_ewa_set_file(infiles) if infiles else None
