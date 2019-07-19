#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from pedigrees.pedigrees import FamilyConnections
from pedigrees.layout import Layout, IndividualWithCoordinates, layout_parser


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
