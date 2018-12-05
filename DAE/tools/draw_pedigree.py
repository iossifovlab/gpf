#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from tqdm import tqdm
import multiprocessing
import functools
import pandas as pd

from pedigrees.pedigree_reader import PedigreeReader
from pedigrees.pedigrees import get_argument_parser
from pedigrees.drawing import OffsetLayoutDrawer, PDFLayoutDrawer
from pedigrees.layout_loader import LayoutLoader
from variants.family import FamiliesBase
from common_reports.common_report import FamiliesReport


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


def main():
    parser = get_argument_parser("Draw PDP.")
    parser.add_argument(
        '--show-id', help='show individual id in pedigree', dest='show_id',
        action='store_true', default=False)
    parser.add_argument(
        '--show-family', help='show family info below pedigree',
        dest='show_family', action='store_true', default=False)

    args = parser.parse_args()

    columns_labels = {
        "family_id": args.family_id,
        "id": args.id,
        "father": args.father,
        "mother": args.mother,
        "sex": args.sex,
        "status": args.status,
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

    pedigrees_df = pd.concat([pedigree.get_pedigree_dataframe()
                              for pedigree in pedigrees])

    families = FamiliesBase(pedigrees_df)
    families.families_build(pedigrees_df)

    phenotype = {
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
        'source': 'phenotype'
    }
    phenotypes = ['affected', 'unaffected', 'unknown']
    roles = [[None]]
    families_report = FamiliesReport(families, phenotype, phenotypes, roles)

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
