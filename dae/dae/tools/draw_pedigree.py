#!/usr/bin/env python
from tqdm import tqdm
import multiprocessing
import functools
import pandas as pd
from box import Box

from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.pedigrees import get_argument_parser
from dae.pedigrees.drawing import OffsetLayoutDrawer, PDFLayoutDrawer
from dae.pedigrees.layout_loader import LayoutLoader
from dae.pedigrees.family import FamiliesData
from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.people_group_info import PeopleGroupInfo
from dae.common_reports.filter import FilterObjects, FilterObject


def draw_family_pedigree(family, show_id=False):
    layout_loader = LayoutLoader(family)
    layout = layout_loader.load()
    if layout is None:
        return 'Invalid coordinates' + " in family " + family.family_id
    else:
        layout_drawer = OffsetLayoutDrawer(layout, 0, 0, show_id)
        return layout_drawer.draw()


def get_layout(family):
    layout_loader = LayoutLoader(family)
    layout = layout_loader.load()
    return {family.family_id: layout}


def draw_pedigree(layouts, show_id, show_family, family):
    layout = layouts[family.family_id]

    if layout is None:
        layout_drawer = OffsetLayoutDrawer(layout, 0, 0)
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

    people_group_info = {
        'domain': {
            'affected': {
                'id': 'affected',
                'name': 'affected',
                'color': '#e35252'
            }
        },
        'unaffected': {
            'id': 'unaffected',
            'name': 'unaffected',
            'color': '#ffffff'
        },
        'default': {
            'id': 'unknown',
            'name': 'unknown',
            'color': '#aaaaaa'
        },
        'source': 'phenotype',
        'name': 'Phenotype'
    }

    people_groups = ['affected', 'unaffected', 'unknown']

    people_group_info = PeopleGroupInfo(
        people_group_info, 'Phenotype', people_groups=people_groups)

    people_groups_info = Box({'people_groups_info': [people_group_info]})

    filters_objects = []

    filter_objects = FilterObjects('Status')
    filter_object1 = FilterObject([])
    filter_object1.add_filter('phenotype', 'unaffected')
    filter_objects.add_filter_object(filter_object1)
    filter_object2 = FilterObject([])
    filter_object2.add_filter('phenotype', 'affected')
    filter_objects.add_filter_object(filter_object2)
    filter_object3 = FilterObject([])
    filter_object3.add_filter('phenotype', 'unknown')
    filter_objects.add_filter_object(filter_object3)
    filters_objects.append(filter_objects)

    families_report = FamiliesReport(
        families, people_groups_info, filters_objects)

    return families_report


def main():
    parser = get_argument_parser(
        "Produce a pedigree drawing in PDF format "
        "from a pedigree file with layout coordinates.")
    parser.add_argument(
        "--layout-column", metavar="l", default="layout",
        help="name of the column containing layout coordinates. "
        "Default to layout.")
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

    args = parser.parse_args()

    columns_labels = {
        "family_id": args.family_id,
        "id": args.id,
        "father": args.father,
        "mother": args.mother,
        "sex": args.sex,
        "status": args.status,
        "role": args.role,
        "layout": args.layout_column
    }
    if args.generated_column:
        columns_labels["generated"] = args.generated_column

    header = args.no_header_order
    if header:
        header = header.split(',')
    delimiter = args.delimiter

    show_id = args.show_id
    show_family = args.show_family

    pedigrees = PedigreeReader().read_file(
        args.file, columns_labels, header, delimiter)

    pdf_drawer = PDFLayoutDrawer(args.output)

    families_report = get_families_report(pedigrees)

    layouts = {}
    with multiprocessing.Pool(processes=args.processes) as pool:
        for layout in tqdm(pool.imap(
            get_layout, sorted(pedigrees, key=lambda x: x.family_id)),
                total=len(pedigrees)):
            layouts.update(layout)

    layout_drawer = OffsetLayoutDrawer(None, 0, 0)
    draw_layout = layout_drawer.draw_families_report(families_report, layouts)
    pdf_drawer.add_pages(draw_layout)

    with multiprocessing.Pool(processes=args.processes) as pool:
        for figure in tqdm(pool.imap(
            functools.partial(draw_pedigree, layouts, show_id, show_family),
            sorted(pedigrees, key=lambda x: x.family_id)),
                total=len(pedigrees)):
            pdf_drawer.add_page(figure)

    pdf_drawer.save_file()


if __name__ == '__main__':
    main()
