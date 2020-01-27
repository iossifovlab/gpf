#!/usr/bin/env python
import sys
import argparse
import pandas as pd

from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_groups import FamiliesGroups
from dae.pedigrees.pedigrees import FamilyConnections
from dae.pedigrees.interval_sandwich import SandwichSolver

from dae.pedigrees.drawing import OffsetLayoutDrawer, PDFLayoutDrawer
from dae.pedigrees.layout import Layout
from dae.pedigrees.family import FamiliesData
from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.people_filters import FilterCollection


def draw_family_pedigree(family, show_id=False):
    layout = Layout.from_family(family)
    if layout is None:
        return 'Invalid coordinates' + " in family " + family.family_id
    else:
        layout_drawer = OffsetLayoutDrawer(layout, 0, 0, show_id)
        return layout_drawer.draw()


def draw_pedigree(layouts, show_id, show_family, family):
    layout = layouts[family.family_id]

    if layout is None:
        layout_drawer = OffsetLayoutDrawer(
            layout, 0, 0, show_id=show_id, show_family=show_family)
        draw_layout = layout_drawer.draw_family(
            family.members,
            title='Invalid coordinates in family ' + family.family_id)
        return draw_layout
    else:
        layout_drawer = OffsetLayoutDrawer(
            layout, 0, 0, show_id=show_id, show_family=show_family)
        draw_layout = layout_drawer.draw(title=family.family_id)
        return draw_layout


def get_families_report(pedigrees):
    pedigrees_df = pd.concat([pedigree.get_pedigree_dataframe()
                              for pedigree in pedigrees])

    families = FamiliesData(pedigrees_df)
    families.families_build(pedigrees_df)

    families_groups = FamiliesGroups(families)
    families_groups.add_predefined_groups(['status'])
    filter_collections = FilterCollection.build_filter_objects(
        families_groups, {'Status': ['status']})

    families_report = FamiliesReport(
        families, families_groups, filter_collections)

    return families_report


def build_layout(family):
    family_connections = FamilyConnections.from_family(family)
    if family_connections is None:
        print(f"Missing family connections for family: {family.family_id}")
        return None

    sandwich_instance = family_connections.create_sandwich_instance()
    intervals = SandwichSolver.solve(sandwich_instance)

    if intervals is None:
        print(f"No intervals for family: {family.family_id}")
        return None

    individuals_intervals = [
        interval for interval in intervals if interval.vertex.is_individual()]

    return Layout(individuals_intervals)


def build_families_layout(families):
    result = {}
    for family in families.values():
        layout = build_layout(family)
        if layout is None:
            print(f"can't draw family {family.family_id}")
            continue
        layout.apply_to_family(family)
        result[family.family_id] = layout
    return result


def draw_family(layout, family):
    assert layout is not None

    layout_drawer = OffsetLayoutDrawer(
        layout, 0, 0, show_id=True, show_family=True)
    draw_layout = layout_drawer.draw(title=family.family_id)
    return draw_layout


def my_draw_pedigree(layout, family, show_id=True, show_family=True):

    if layout is None:
        layout_drawer = OffsetLayoutDrawer(
            layout, 0, 0, show_id=show_id, show_family=show_family)

        draw_layout = layout_drawer.draw_family_table(
            family,
            title='Invalid coordinates in family ' + family.family_id)
        return draw_layout
    else:
        layout_drawer = OffsetLayoutDrawer(
            layout, 0, 0, show_id=show_id, show_family=show_family)
        draw_layout = layout_drawer.draw(title=family.family_id)
        return draw_layout


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
    parser.add_argument(
        '--show-id', help='show individual id in pedigree', dest='show_id',
        action='store_true', default=False)
    parser.add_argument(
        '--show-family', help='show family info below pedigree',
        dest='show_family', action='store_true', default=False)
    parser.add_argument(
        "--generated-column", metavar="m", default="generated",
        help="name of the column that contains an "
             "indicator for generated individuals")
    parser.add_argument(
        '--processes', type=int, default=4, dest='processes',
        help='Number of processes', action='store'
    )

    argv = parser.parse_args(argv)

    show_id = argv.show_id
    show_family = argv.show_family

    filename, params = FamiliesLoader.parse_cli_arguments(argv)
    families_loader = FamiliesLoader(filename, params=params)
    families = families_loader.load()
    # layouts = build_families_layout(families)

    pdf_drawer = PDFLayoutDrawer(argv.output)

    # families_report = get_families_report(families)

    # layouts = {}
    # with multiprocessing.Pool(processes=argv.processes) as pool:
    #     for layout in tqdm(pool.imap(
    #         get_layout, sorted(families, key=lambda x: x.family_id)),
    #             total=len(families)):
    #         layouts.update(layout)

    figures = []
    for family_id, family in families.items():
        print(family_id)
        layout = build_layout(family)
        if layout is None:
            print(f"can't draw family {family.family_id}")
        else:
            layout.apply_to_family(family)

        fig = my_draw_pedigree(layout, family)
        figures.append(fig)

        if len(figures) == 100:
            break

    pdf_drawer.add_pages(figures)

    # for family_id, layout in layouts.items():
    #     family = families[family_id]

    #     fig = draw_family(layout, family)
    #     figures.append(fig)

    #     if len(figures) == 10:
    #         break

    # with multiprocessing.Pool(processes=argv.processes) as pool:
    #     for figure in tqdm(pool.imap(
    #         functools.partial(draw_pedigree, layouts, show_id, show_family),
    #         sorted(families, key=lambda x: x.family_id)),
    #             total=len(families)):
    #         pdf_drawer.add_page(figure)

    pdf_drawer.save_file()


if __name__ == '__main__':
    main()
