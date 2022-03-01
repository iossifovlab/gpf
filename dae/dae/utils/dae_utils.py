import os
import re

SUB_COMPLEX_RE = re.compile(r"^(sub|complex|comp)\(([NACGT]+)->([NACGT]+)\)$")
INS_RE = re.compile(r"^ins\(([NACGT]+)\)$")
DEL_RE = re.compile(r"^del\((\d+)\)$")


def cached(prop):
    cached_val_name = "_" + prop.__name__

    def wrap(self):
        if getattr(self, cached_val_name, None) is None:
            setattr(self, cached_val_name, prop(self))
        return getattr(self, cached_val_name)
    return wrap


def dae2vcf_variant(chrom, position, var, genome):
    match = SUB_COMPLEX_RE.match(var)
    if match:
        return position, match.group(2), match.group(3)

    match = INS_RE.match(var)
    if match:
        alt_suffix = match.group(1)
        reference = genome.get_sequence(chrom, position - 1, position - 1)
        return position - 1, reference, reference + alt_suffix

    match = DEL_RE.match(var)
    if match:
        count = int(match.group(1))
        reference = genome.get_sequence(
            chrom, position - 1, position + count - 1
        )
        assert len(reference) == count + 1, reference
        return position - 1, reference, reference[0]

    raise NotImplementedError("weird variant: " + var)


def split_iterable(iterable, max_chunk_length=50):
    i = 0
    result = []

    for value in iterable:
        i += 1
        result.append(value)

        if i == max_chunk_length:
            yield result
            result = []
            i = 0

    if i != 0:
        yield result


def join_line(ln, sep="\t"):
    lm = map(lambda v: "; ".join(v) if isinstance(v, list) else v, ln)
    tl = map(lambda v: "" if v is None or v == "None" else str(v), lm)
    return sep.join(tl) + "\n"


def get_pheno_db_dir(dae_config):
    if dae_config is not None:
        if dae_config.phenotype_data is None or \
                dae_config.phenotype_data.dir is None:
            pheno_data_dir = os.path.join(
                dae_config.conf_dir, "pheno")
        else:
            pheno_data_dir = dae_config.phenotype_data.dir
    else:
        pheno_data_dir = os.path.join(os.environ.get("DAE_DB_DIR"), "pheno")

    return pheno_data_dir


def get_pheno_browser_images_dir(dae_config=None):
    pheno_db_dir = os.environ.get(
        "DAE_PHENODB_DIR",
        get_pheno_db_dir(dae_config)
    )
    browser_images_path = os.path.join(pheno_db_dir, "images")
    return browser_images_path


def get_pheno_base_url():
    url_prefix = ""
    gpf_prefix = os.environ.get("GPF_PREFIX")
    if gpf_prefix is not None:
        url_prefix = f"/{gpf_prefix}"
    return f"{url_prefix}/static/images/"
