#!/usr/bin/env python
import sys
import os
import argparse
import logging
import glob
from pathlib import Path
import yaml

from dae.gene.gene_term import read_ewa_set_file, read_gmt_file, \
    read_mapping_file
from dae.gene.gene_sets_db import GeneSet, \
    build_gene_set_collection_from_file

logger = logging.getLogger("create_sqlite_gene_set")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-V", action="count", default=0)
    parser.add_argument(
        "--resource",
        dest="resource",
        help="path to genomic_resource.yaml to use",
        default=None
    )
    parser.add_argument(
        "--format",
        dest="format",
        help="format of gene set (map, gmt, directory)",
        default=None
    )
    parser.add_argument(
        "--filename",
        dest="filename",
        help="path to gmt or map file",
        default=None
    )
    parser.add_argument(
        "--directory",
        dest="directory",
        help="path to directory collection data",
        default=None
    )
    parser.add_argument(
        "--output",
        dest="output",
        help="where to write sqlite DB file",
        default="collection_db"
    )

    argv = parser.parse_args(argv)
    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if argv.resource is not None:
        with open(argv.resource) as file:
            content = file.read()
            resource_config = yaml.safe_load(content)
            base_dir = os.path.dirname(argv.resource)
            collection_id = resource_config["id"]
            collection_format = resource_config["format"]
            if collection_format == "map":
                filename = resource_config["filename"]
                filepath = os.path.join(base_dir, filename)
                names_filename = filename[:-4] + "names.txt"
                names_filepath = os.path.join(base_dir, names_filename)
                names_file = None
                if os.path.exists(names_filepath):
                    names_file = open(names_filepath)
                gene_terms = read_mapping_file(
                    open(filepath),
                    names_file
                )
            elif collection_format == "gmt":
                filename = resource_config["filename"]
                filepath = os.path.join(base_dir, filename)
                gene_terms = read_gmt_file(open(filepath))
            elif collection_format == "directory":
                directory = os.path.join(
                    base_dir, resource_config["directory"]
                )
                filepaths = glob.glob(f"{directory}/*.txt")
                files = [
                    (Path(f).stem, open(f))
                    for f in filepaths
                ]
                gene_terms = read_ewa_set_file(files)
            else:
                raise ValueError("Invalid collection format type")
    elif argv.format is not None:
        raise NotImplementedError()
    else:
        raise ValueError("Invalid arguments")

    db = build_gene_set_collection_from_file(
        argv.output,
        collection_id=collection_id,
        collection_format="sqlite"
    )

    for key, value in gene_terms.tDesc.items():
        syms = list(gene_terms.t2G[key].keys())
        gene_set = GeneSet(key, value, syms)
        db.add_gene_set(gene_set)


if __name__ == "__main__":

    main(sys.argv[1:])
