import argparse
import os
import sys
from typing import Optional

from dae.gene_scores.gene_scores import (
    GeneScoresDb,
    build_gene_score_from_resource,
)
from dae.genomic_resources.cli import (
    _create_proto,
    _find_resource,
    _run_resource_stats_command,
)
from dae.genomic_resources.genomic_scores import build_score_from_resource
from dae.genomic_resources.histogram import (
    NullHistogram,
)
from dae.genomic_resources.repository import (
    GR_CONTENTS_FILE_NAME,
    ReadWriteRepositoryProtocol,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
    get_default_grr_definition,
)
from dae.utils.fs_utils import find_directory_with_a_file
from dae.utils.verbosity_configuration import VerbosityConfiguration


def parse_cli_arguments() -> argparse.ArgumentParser:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(
        description="liftover VCF variants")

    VerbosityConfiguration.set_arguments(parser)

    # parser.add_argument("-o", "--output-prefix", help="output filename prefix")

    return parser


def main(
        argv: Optional[list[str]] = None,
) -> None:
    """Liftover dae variants tool main function."""
    # pylint: disable=too-many-locals,too-many-statements
    if argv is None:
        argv = sys.argv[1:]

    parser = parse_cli_arguments()
    args = parser.parse_args(argv)

    VerbosityConfiguration.set(args)

    repo_path = find_directory_with_a_file(GR_CONTENTS_FILE_NAME)
    if repo_path is None:
        print("Can't find repository starting from: %s", os.getcwd())
        sys.exit(1)

    repo_url = str(repo_path)
    print(f"working with repository: {repo_url}")

    # extra_definition_path = args.grr
    # if extra_definition_path:
    #     if not os.path.exists(extra_definition_path):
    #         raise FileNotFoundError(
    #             f"Definition {extra_definition_path} not found!",
    #         )
    #     extra_definition = load_definition_file(extra_definition_path)
    # else:

    extra_definition = get_default_grr_definition()
    grr_definition = {
        "id": "cli_grr",
        "type": "group",
        "children": [
            {
                "id": "local",
                "type": "dir",
                "directory": repo_url,
            },
            extra_definition,
        ],
    }

    repo = build_genomic_resource_repository(definition=grr_definition)

    # proto = _create_proto(repo_url, args.extra_args)
    proto = _create_proto(repo_url)

    if not isinstance(proto, ReadWriteRepositoryProtocol):
        raise TypeError(
            f"resource management works with RW protocols; "
            f"{proto.proto_id} ({proto.scheme}) is read only")

    status = _run_resource_stats_command(
        repo, proto, repo_url, **vars(args))

    # dry_run = cast(bool, **vars(args).get("dry_run", False))
    # if dry_run:
    #     print(status)

    res = _find_resource(proto, repo_url, **vars(args))
    if res is None:
        print("Resource not found...")
        sys.exit(1)

    assert res.config is not None
    if res.config.get("type") == "gene_score":
        gene_score = build_gene_score_from_resource(res)
        score_descs = GeneScoresDb.build_descs_from_score(gene_score)

        for score_desc in score_descs:
            with proto.open_raw_file(
                res,
                gene_score.get_histogram_image_filename(score_desc.score_id),
                mode="wb",
            ) as outfile:
                score_desc.hist.plot(
                    outfile,
                    score_desc.score_id,
                    score_desc.small_values_desc,
                    score_desc.large_values_desc,
                )
    else:
        genomic_score = build_score_from_resource(res)
        score_ids = genomic_score.get_all_scores()

        for score_id in score_ids:
            hist = genomic_score.get_score_histogram(score_id)
            if not isinstance(hist, NullHistogram):
                with proto.open_raw_file(
                    res,
                    genomic_score.get_histogram_image_filename(score_id),
                    mode="wb",
                ) as outfile:
                    hist.plot(
                        outfile,
                        score_id,
                        genomic_score.score_definitions[score_id].small_values_desc,
                        genomic_score.score_definitions[score_id].large_values_desc,
                    )


main()
