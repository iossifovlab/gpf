#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from tqdm import tqdm
import multiprocessing

from pedigrees.pedigree_reader import PedigreeReader
from pedigrees.pedigrees import get_argument_parser, FamilyConnections
from pedigrees.interval_sandwich import SandwichSolver
from pedigrees.layout import Layout
from pedigrees.layout_saver import LayoutSaver


def save_pedigree(family):
    family_connections = FamilyConnections.from_pedigree(family)
    if family_connections is None:
        print(family.family_id)
        print("Missing members")
        return (family, "Missing members")
    sandwich_instance = family_connections.create_sandwich_instance()
    intervals = SandwichSolver.solve(sandwich_instance)

    if intervals is None:
        print(family.family_id)
        print("No intervals")
        return (family, "No intervals")
    if intervals:
        individuals_intervals = [interval for interval in intervals
                                 if interval.vertex.is_individual()]

        # print(family.family_id)
        layout = Layout(individuals_intervals)
        return (family, layout)


def main():
    parser = get_argument_parser("Save PDP.")
    args = parser.parse_args()

    columns_labels = {
        "family_id": args.family_id,
        "id": args.id,
        "father": args.father,
        "mother": args.mother,
        "sex": args.sex,
        "status": args.status,
        "role": args.role,
        "layout": ""
    }
    header = args.no_header_order
    if header:
        header = header.split(',')
    delimiter = args.delimiter

    pedigrees = PedigreeReader().read_file(
        args.file, columns_labels, header, delimiter)

    layout_saver = LayoutSaver(
        args.file, args.output, args.generated_column, args.layout_column)

    with multiprocessing.Pool(processes=args.processes) as pool:
        for family_layout in tqdm(pool.imap(
                save_pedigree, sorted(pedigrees, key=lambda x: x.family_id)),
                total=len(pedigrees)):

            layout_saver.write(family_layout[0], family_layout[1])

    layout_saver.save(columns_labels, header, delimiter)


if __name__ == '__main__':
    main()
