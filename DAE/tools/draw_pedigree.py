#!/usr/bin/env python
import re
from tqdm import tqdm
import multiprocessing
import functools
import pandas as pd

from pedigrees.pedigree_reader import PedigreeReader
from pedigrees.pedigrees import get_argument_parser, FamilyConnections
from pedigrees.drawing import OffsetLayoutDrawer, PDFLayoutDrawer
from pedigrees.layout import Layout, IndividualWithCoordinates, layout_parser
from variants.family import FamiliesBase
from common_reports.common_report import FamiliesReport


class LayoutLoader(object):

    def __init__(self, family):
        self.family = family
        self.family_connections = FamilyConnections.from_pedigree(
            family, add_missing_members=False)

    def get_positions_from_family(self):
        positions = {}
        if self.family_connections is None:
            layout = layout_parser(self.family.members[0].layout)
            if layout is None:
                return None
        individuals = self.family_connections.get_individuals()
        for individual in individuals:
            layout = layout_parser(individual.member.layout)
            if layout is None:
                return None
            level = layout['level']
            x = layout['x']
            y = layout['y']

            if level not in positions:
                positions[level] = []
            positions[level].append(IndividualWithCoordinates(
                individual, x, y))

        individuals = [[]] * len(positions)
        for level, iwc in positions.items():
            individuals[level - 1] = iwc

        individuals = [sorted(level, key=lambda x: x.x)
                       for level in individuals]

        return individuals

    def load(self):
        positions = self.get_positions_from_family()
        if positions is None:
            return None
        layout = Layout.get_layout_from_positions(positions)

        return layout


def draw_family_pedigree(family, show_id=False):
    layout_loader = LayoutLoader(family)
    layout = layout_loader.load()
    if layout is None:
        return 'Invalid coordinates' + " in family " + family.family_id
    else:
        layout_drawer = OffsetLayoutDrawer(layout, 0, 0, show_id)
        return layout_drawer.draw()


def draw_pedigree(show_id, show_family, family):
    layout_loader = LayoutLoader(family)
    layout = layout_loader.load()
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

    with multiprocessing.Pool(processes=args.processes) as pool:
        for figure in tqdm(pool.imap(
            functools.partial(draw_pedigree, show_id, show_family),
            sorted(pedigrees, key=lambda x: x.family_id)),
                total=len(pedigrees)):
            pdf_drawer.add_page(figure)

    pdf_drawer.save_file()


if __name__ == '__main__':
    main()
