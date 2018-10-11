#!/usr/bin/env python
from pedigrees.pedigree_reader import PedigreeReader
from pedigrees.pedigrees import get_argument_parser, FamilyConnections
from pedigrees.drawing import OffsetLayoutDrawer, PDFLayoutDrawer
from pedigrees.layout import Layout, IndividualWithCoordinates


class LayoutLoader(object):

    def __init__(self, family):
        self.family = family
        self.family_connections = FamilyConnections.from_pedigree(
            family, add_missing_members=False)

    def get_positions_from_family(self):
        positions = {}
        if self.family_connections is None:
            position = self.family.members[0].layout.split(":")
            if len(position) == 1:
                return position[0]
            else:
                return ''
        individuals = self.family_connections.get_individuals()
        for individual in individuals:
            position = individual.member.layout.split(":")
            if len(position) == 1:
                return position[0]
            position[1] = position[1].split(",")

            level = int(position[0])
            x = float(position[1][0])
            y = float(position[1][1])

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
        if isinstance(positions, str):
            return positions
        layout = Layout.get_layout_from_positions(positions)

        return layout


def main():
    parser = get_argument_parser("Draw PDP.")
    parser.add_argument(
        '--show-id', help='show individual id in pedigree', dest='show_id',
        action='store_true', default=False)

    args = parser.parse_args()

    columns_labels = {
        "family_id": args.family_id,
        "id": args.id,
        "father": args.father,
        "mother": args.mother,
        "sex": args.sex,
        "effect": args.effect,
        "layout": args.layout_column
    }
    header = args.no_header_order
    if header:
        header = header.split(',')
    delimiter = args.delimiter

    show_id = args.show_id

    pedigrees = PedigreeReader().read_file(
        args.file, columns_labels, header, delimiter)

    pdf_drawer = PDFLayoutDrawer(args.output)

    for family in sorted(pedigrees, key=lambda x: x.family_id):
        layout_loader = LayoutLoader(family)
        layout = layout_loader.load()
        if isinstance(layout, str):
            pdf_drawer.add_error_page(
                family.members,
                layout + " in family " + family.family_id)
        else:
            layout_drawer = OffsetLayoutDrawer(layout, 0, 0, show_id)
            pdf_drawer.add_page(layout_drawer.draw(), family.family_id)

    pdf_drawer.save_file()


if __name__ == '__main__':
    main()
