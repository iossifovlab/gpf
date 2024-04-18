#!/usr/bin/env python
"""Tool to draw pedigrees defined in a file."""
import argparse
import logging
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt

from dae.common_reports.family_report import FamiliesReport
from dae.configuration.gpf_config_parser import FrozenBox
from dae.pedigrees.drawing import OffsetLayoutDrawer, PDFLayoutDrawer
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.layout import Layout
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import PersonSetCollection

mpl.use("PS")
plt.ioff()


logger = logging.getLogger("draw_pedigree")


def build_families_report(families: FamiliesData) -> FamiliesReport:
    """Build a family report based on affected status."""
    status_collection_config = {
        "id": "status",
        "name": "Affected status",
        "domain": [
            {
                "id": "affected",
                "name": "affected",
                "values": ["affected"],
                "color": "#e35252",
            },
            {
                "id": "unaffected",
                "name": "unaffected",
                "values": ["unaffected"],
                "color": "#ffffff",
            },
        ],
        "default": {
            "id": "unspecified",
            "name": "unspecified",
            "color": "#aaaaaa",
        },
        "sources": [{"from": "pedigree", "column": "status"}],
    }
    status_collection_config = FrozenBox(
        status_collection_config,
    )
    status_collection = PersonSetCollection.from_families(
        status_collection_config, families,
    )
    return FamiliesReport.from_families_data(
        families, [status_collection], draw_all_families=False)


def draw_pedigree(layout, title, show_family=True, tags=None):

    layout_drawer = OffsetLayoutDrawer(
        layout, show_family=show_family,
    )
    figure = layout_drawer.draw(title=title, tags=tags)
    return figure


def build_family_layout(family):
    # layout = Layout.from_family_layout(family)
    # if layout is None:
    return Layout.from_family(family)


def draw_families_report(families):
    """Draw families from families report."""
    families_report = build_families_report(families)
    assert len(families_report.families_counters) == 1

    family_counters = list(families_report.families_counters.values())[0]
    logger.info("total number family types: %s", len(family_counters.counters))

    for family_counter in family_counters.counters.values():
        family_id = family_counter.family
        family = families[family_id]
        layout = build_family_layout(family)
        logger.info(
            "drawing %s; list of families in this category: %s",
            family, ",".join(family_counter.families))

        if len(family_counter.families) > 5:
            count = len(family_counter.families)
            title = f"Number of families: {count}"
        else:
            title = ", ".join(family_counter.families)
        figure = draw_pedigree(layout, title=title, tags=family.tag_labels)
        yield figure


def draw_families(families):
    """Draw families."""
    for family_id, family in families.items():
        layout = build_family_layout(family)

        figure = draw_pedigree(layout, title=family_id, tags=family.tag_labels)
        yield figure


def main(argv=None):
    """Run the CLI for draw_pedigree tool."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Produce a pedigree drawing in PDF format "
        "from a pedigree file with layout coordinates.",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--verbose", "-V", action="count", default=0)

    FamiliesLoader.cli_arguments(parser)

    parser.add_argument(
        "--output",
        "-o",
        metavar="o",
        help="the output filename file",
        default="output.pdf",
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="report",
        dest="mode",
        help="mode of drawing; supported modes are `families` and `report`; "
        "defaults: `report`",
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

    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    filenames, params = FamiliesLoader.parse_cli_arguments(argv)
    filename = filenames[0]

    families_loader = FamiliesLoader(filename, **params)
    families = families_loader.load()

    mode = argv.mode
    assert mode in ("families", "report")
    logger.warning("using mode: %s", mode)
    if mode == "report":
        generator = draw_families_report(families)
    else:
        generator = draw_families(families)

    with PDFLayoutDrawer(argv.output) as pdf_drawer:

        for fig in generator:
            pdf_drawer.savefig(fig)
            plt.close(fig)


if __name__ == "__main__":
    main()
