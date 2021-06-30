#!/usr/bin/env python
import os
import logging
import yaml
import argparse
import pathlib
from glob import glob
from urllib.parse import urlparse
from subprocess import call

from dae.genomic_resources.resources import GenomicResourceGroup, \
    GenomicResource
from dae.annotation.tools.annotator_config import AnnotationConfigParser

logger = logging.getLogger(__name__)


def main(argv=None):
    description = (
        "Tool for creating/updating the metadata required for a "
        "genomic resource repository to be created."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose', '-V', '-v', action='count', default=0)

    args = parser.parse_args(argv)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    logger.info("Gathering genomic resources")

    root_path = pathlib.Path(".").absolute()
    conf_files = glob(
        os.path.join(root_path, "**", "genomic_score.yaml"), recursive=True
    )
    root_url = root_path.as_uri()
    root = GenomicResourceGroup("root", root_url)
    for conf_path in conf_files:
        score_path = conf_path[len(root_path.as_posix()):]
        score_path = score_path.strip('/').split('/')
        assert len(score_path) >= 1, score_path
        curr_group = root
        curr_path = ""
        for group in score_path[:-2]:
            curr_path += f"/{group}"
            curr_path = curr_path.strip("/")
            if group not in curr_group.children:
                url = pathlib.Path(curr_path).absolute().as_uri()
                resource = GenomicResourceGroup(curr_path, url)
                curr_group.add_child(resource)
            curr_group = curr_group.children[group]
        curr_path += f"/{score_path[-2]}"
        config = AnnotationConfigParser.load_annotation_config(
            conf_path
        )
        score_url = pathlib.Path(curr_path).absolute().as_uri()
        score = GenomicResource(config, score_url, None, None)
        curr_group.add_child(score)

    repo_content = dict()

    logger.info("Writing resources to CONTENT metadata")

    def add_resource_to_content_dict(resource, section):
        section["id"] = resource.get_id()
        if isinstance(resource, GenomicResourceGroup):
            section["type"] = "group"
            section["children"] = []
            for child in resource.get_children():
                child_section = dict()
                add_resource_to_content_dict(child, child_section)
                section["children"].append(child_section)
        else:
            section["type"] = "resource"

    add_resource_to_content_dict(root, repo_content)

    with open("CONTENT.yaml", "w") as out:
        yaml.dump(repo_content, out, default_flow_style=False, sort_keys=False)

    logger.info("Generating MANIFEST files")

    for resource in root.get_resources():
        cwd = urlparse(resource.get_url()).path
        call(
            "find . -type f \\( ! -iname \"MANIFEST\" \\)  "
            "-exec sha256sum {} \\; | sed \"s|\\s\\./||\""
            "> MANIFEST",
            cwd=cwd,
            shell=True
        )

    logger.info("Done")


if __name__ == "__main__":
    main()
