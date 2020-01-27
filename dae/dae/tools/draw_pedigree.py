#!/usr/bin/env python
import sys
import argparse

import matplotlib as mpl; mpl.use('PS')  # noqa
import matplotlib.pyplot as plt; plt.ioff()  # noqa

from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_groups import FamiliesGroups

from dae.pedigrees.drawing import OffsetLayoutDrawer, PDFLayoutDrawer
from dae.pedigrees.layout import Layout
from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.people_filters import FilterCollection


def build_families_report(families):

    families_groups = FamiliesGroups(families)
    # families_groups.add_predefined_groups(['status'])
    families_groups.add_predefined_groups(
            ['status', 'sex', 'role', 'role.sex', 'family_size'])
    filter_collections = FilterCollection.build_filter_objects(
        families_groups, {'Status': ['status']})

    families_report = FamiliesReport(
        ['status'], families_groups, filter_collections)

    return families_report


def draw_family(layout, family):
    assert layout is not None

    layout_drawer = OffsetLayoutDrawer(
        layout, 0, 0, show_id=True, show_family=True)
    draw_layout = layout_drawer.draw(title=family.family_id)
    return draw_layout


def draw_pedigree(layout, title, show_id=True, show_family=True):

    layout_drawer = OffsetLayoutDrawer(
        layout, 0, 0, show_id=show_id, show_family=show_family)
    figure = layout_drawer.draw(title=title)
    return figure


def draw_families_report(families):
    families_report = build_families_report(families)
    assert len(families_report.families_counters) == 1
    family_counters = families_report.families_counters[0]

    for family_counter in family_counters.counters.values():
        family = family_counter.family
        layout = Layout.from_family(family)

        if len(family_counter.families) > 5:
            count = len(family_counter.families)
            title = f'Number of families: {count}'
        else:
            title = ', '.join([f.family_id for f in family_counter.families])

        figure = draw_pedigree(layout, title=title)
        yield figure


def draw_families(families):
    for family_id, family in families.items():
        layout = Layout.from_family(family)
        if layout is None:
            print(f"can't draw family {family.family_id}")
        else:
            layout.apply_to_family(family)

        figure = draw_pedigree(layout, title=family.family_id)
        yield figure


def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(
            description="Produce a pedigree drawing in PDF format "
            "from a pedigree file with layout coordinates.",
            conflict_handler='resolve',
            formatter_class=argparse.RawDescriptionHelpFormatter)

    FamiliesLoader.cli_arguments(parser)

    parser.add_argument(
        "--output", metavar="o", help="the output filename file",
        default="output.pdf")

    # parser.add_argument(
    #     '--show-id', help='show individual id in pedigree', dest='show_id',
    #     action='store_true', default=False)
    # parser.add_argument(
    #     '--show-family', help='show family info below pedigree',
    #     dest='show_family', action='store_true', default=False)

    parser.add_argument(
        '--mode', type=str, default='families', dest='mode',
        help='mode of drawing; supported modes are `families` and `report`; '
        'defaults: families'
    )

    argv = parser.parse_args(argv)

    filename, params = FamiliesLoader.parse_cli_arguments(argv)
    families_loader = FamiliesLoader(filename, params=params)
    families = families_loader.load()

    mode = argv.mode
    assert mode in ('families', 'report')
    if mode == 'report':
        generator = draw_families_report(families)
    else:
        generator = draw_families(families)

    with PDFLayoutDrawer(argv.output) as pdf_drawer:

        for fig in generator:
            pdf_drawer.savefig(fig)
            plt.close(fig)


if __name__ == '__main__':
    main()
