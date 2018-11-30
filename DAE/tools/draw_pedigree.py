#!/usr/bin/env python
import re
from tqdm import tqdm

from pedigrees.pedigree_reader import PedigreeReader
from pedigrees.pedigrees import get_argument_parser, FamilyConnections
from pedigrees.drawing import OffsetLayoutDrawer, PDFLayoutDrawer
from pedigrees.layout import Layout, IndividualWithCoordinates


class LayoutLoader(object):

    def __init__(self, family):
        self.family = family
        self.family_connections = FamilyConnections.from_pedigree(
            family, add_missing_members=False)

    def parse_layout(self, layout):
        layout_groups = re.search(
            r'(?P<level>\d):(?P<x>\d*\.?\d+),(?P<y>\d*\.?\d+)', str(layout))
        if layout_groups:
            layout_groups = layout_groups.groupdict()
            layout_groups['level'] = int(layout_groups['level'])
            layout_groups['x'] = float(layout_groups['x'])
            layout_groups['y'] = float(layout_groups['y'])
        return layout_groups

    def get_positions_from_family(self):
        positions = {}
        if self.family_connections is None:
            layout = self.parse_layout(self.family.members[0].layout)
            if layout is None:
                return None
        individuals = self.family_connections.get_individuals()
        for individual in individuals:
            layout = self.parse_layout(individual.member.layout)
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

    progress_bar = tqdm(total=len(pedigrees))

    for family in sorted(pedigrees, key=lambda x: x.family_id):
        progress_bar.update(1)

        layout_loader = LayoutLoader(family)
        layout = layout_loader.load()
        if layout is None:
            layout_drawer = OffsetLayoutDrawer(layout, 0, 0)
            pdf_drawer.add_page(
                layout_drawer.draw_family(family.members),
                'Invalid coordinates in family ' + family.family_id)
        else:
            layout_drawer = OffsetLayoutDrawer(
                layout, 0, 0, show_id=show_id, show_family=show_family)
            pdf_drawer.add_page(layout_drawer.draw(), family.family_id)

    progress_bar.close()

    pdf_drawer.save_file()


if __name__ == '__main__':
    main()
