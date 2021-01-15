#!/usr/bin/env python
import sys
import argparse

from dae.pedigrees.loader import FamiliesLoader

from dae.pedigrees.drawing import OffsetLayoutDrawer, PDFLayoutDrawer
from dae.pedigrees.layout import Layout
from dae.common_reports.family_report import FamiliesReport
from dae.configuration.gpf_config_parser import FrozenBox
from dae.person_sets import PersonSetCollection

import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.use("PS")  # noqa
plt.ioff()  # noqa


def build_families_report(families):
    status_collection_config = {
        "id": "status",
        "name": "Affected status",
        "domain": [
            {
                "id": "affected",
                "name": "affected",
                "values": ["affected"],
                "color": "#e35252"
            },
            {
                "id": "unaffected",
                "name": "unaffected",
                "values": ["unaffected"],
                "color": "#ffffff"
            }
        ],
        "default": {
            "id": "unspecified",
            "name": "unspecified",
            "color": "#aaaaaa"
        },
        "sources": [{"from": "pedigree", "column": "status"}]
    }
    status_collection_config = FrozenBox(
        status_collection_config
    )
    status_collection = PersonSetCollection.from_families(
        status_collection_config, families
    )
    return FamiliesReport(families, [status_collection])


def draw_pedigree(layout, title, show_id=True, show_family=True):

    layout_drawer = OffsetLayoutDrawer(
        layout, 0, 0, show_id=show_id, show_family=show_family
    )
    figure = layout_drawer.draw(title=title)
    return figure


def build_family_layout(family):
    # layout = Layout.from_family_layout(family)
    # if layout is None:
    return Layout.from_family(family)


def draw_families_report(families):
    families_report = build_families_report(families)
    assert len(families_report.families_counters) == 1
    family_counters = families_report.families_counters[0]
    print("total number:", len(family_counters.counters))

    for index, family_counter in enumerate(family_counters.counters.values()):
        family = family_counter.family
        layout = build_family_layout(family)
        if len(family_counter.families) > 5:
            count = len(family_counter.families)
            title = f"Number of families: {count}"
        else:
            title = ", ".join([f.family_id for f in family_counter.families])

        figure = draw_pedigree(layout, title=title)
        yield figure
        remainder = (index + 1) % 10
        if remainder == 0:
            print(".", end="", file=sys.stderr)
        remainder = (index + 1) % 100
        if remainder == 0:
            print("", file=sys.stderr)

    print("", file=sys.stderr)


def draw_families(families):
    for family_id, family in families.items():
        layout = build_family_layout(family)

        figure = draw_pedigree(layout, title=family.family_id)
        yield figure


def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(
        description="Produce a pedigree drawing in PDF format "
        "from a pedigree file with layout coordinates.",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

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

    filename, params = FamiliesLoader.parse_cli_arguments(argv)
    families_loader = FamiliesLoader(filename, **params)
    families = families_loader.load()

    mode = argv.mode
    assert mode in ("families", "report")
    print("mode:", mode)
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
