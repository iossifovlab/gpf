import argparse
import sys
from typing import Optional

import numpy as np
import yaml

from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    CategoricalHistogramConfig,
    NullHistogram,
    NullHistogramConfig,
    NumberHistogram,
    NumberHistogramConfig,
)
from dae.utils.verbosity_configuration import VerbosityConfiguration


def parse_cli_arguments() -> argparse.ArgumentParser:
    """Create CLI parser."""
    parser = argparse.ArgumentParser(
        description="liftover VCF variants")

    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument(
        "histogram_conf", help="histogram configuration",
    )

    parser.add_argument(
        "-o", "--output-prefix", help="output filename prefix",
        default="transmitted")

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

    with open(args.histogram_conf) as infile, \
            open(f"{args.output_prefix}.png", "wb") as outfile:
        data = yaml.load(infile, yaml.Loader)

        histogram_dict = data["config"]
        if histogram_dict["type"] == "number":
            number_histogram_conf = NumberHistogramConfig.from_dict(histogram_dict)
            NumberHistogram(
                number_histogram_conf,
                np.array(data["bins"]),
                np.array(data["bars"]),
            ).plot(outfile, "sample_score_id")
        elif histogram_dict["type"] == "categorical":
            categorical_histogram_conf = CategoricalHistogramConfig.from_dict(histogram_dict)
            CategoricalHistogram(
                categorical_histogram_conf,  # is it enough??
            ).plot(outfile, "sample_score_id")
        else:
            null_histogram_conf = NullHistogramConfig.from_dict(histogram_dict)
            NullHistogram(
                null_histogram_conf,
            ).plot(outfile, "sample_score_id")


if __name__ == "__main__":
    main()
