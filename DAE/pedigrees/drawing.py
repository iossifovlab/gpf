from __future__ import division
from __future__ import unicode_literals
from past.utils import old_div
from builtins import object
from copy import deepcopy
import math

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.path import Path
from matplotlib.backends.backend_pdf import PdfPages

from variants.attributes import Sex


class PDFLayoutDrawer(object):

    def __init__(self, filename):
        self._filename = filename
        self._pages = []

    def add_page(self, figure, title=None):
        if title:
            figure.text(0.5, 0.9, title, horizontalalignment="center")
        self._pages.append(figure)

    def save_file(self):
        with PdfPages(self._filename) as pdf:
            for page in self._pages:
                pdf.savefig(page)
                plt.close(page)


class OffsetLayoutDrawer(object):

    def __init__(
            self, layout, x_offset, y_offset, show_id=False,
            show_family=False):
        self._x_offset = x_offset
        self._y_offset = y_offset
        self._layout = deepcopy(layout)
        self.show_id = show_id
        self.show_family = show_family
        if self._layout is not None:
            self._horizontal_mirror_layout()

    def draw(self, figure=None):
        if figure is None:
            figure = plt.figure()

        pedigree_axes_rect = (0.35, 0.33, 0.33, 0.33)
        if self.show_family:
            pedigree_axes_rect = (0.35, 0.45, 0.3, 0.45)

        ax_pedigree = figure.add_axes(pedigree_axes_rect)
        ax_pedigree.axis("off")
        ax_pedigree.set_aspect(aspect="equal", adjustable="datalim", anchor="C")
        ax_pedigree.autoscale_view()

        self._draw_lines(ax_pedigree)
        self._draw_rounded_lines(ax_pedigree)

        self._draw_members(ax_pedigree)

        ax_pedigree.plot()

        if self.show_family:
            ax_family = figure.add_axes((0.1, 0.1, 0.8, 0.3))
            ax_family.axis("off")
            ax_family.set_aspect(
                aspect="equal", adjustable="datalim", anchor="C")
            ax_family.autoscale_view()

            family = [member.individual.member
                      for layer in self._layout.positions for member in layer]

            self._draw_family(ax_family, family)

            ax_family.plot()

        return figure

    def draw_family(self, family):
        figure, ax = plt.subplots()
        ax.axis("off")

        self._draw_family(figure, family)

        return figure

    def _draw_lines(self, axes):
        for line in self._layout.lines:
            if not line.curved:
                axes.add_line(mlines.Line2D(
                    [line.x1 + self._x_offset, line.x2 + self._x_offset],
                    [line.y1 + self._y_offset, line.y2 + self._y_offset],
                    color="black"
                ))

    def _draw_rounded_lines(self, axes):
        elementwise_sum = lambda x, y: tuple([x[0] + y[0], x[1] + y[1]])

        for line in self._layout.lines:
            if line.curved:
                offset = (self._x_offset, self._y_offset)
                verts = [
                    elementwise_sum(line.curve_p0(), offset),
                    elementwise_sum(line.curve_p1(), offset),
                    elementwise_sum(line.curve_p2(), offset),
                    elementwise_sum(line.curve_p3(), offset)
                ]

                codes = [
                    Path.MOVETO,
                    Path.CURVE4,
                    Path.CURVE4,
                    Path.CURVE4
                ]

                path = Path(verts, codes)

                axes.add_patch(mpatches.PathPatch(path, facecolor='none'))

                # line = ()

    def _draw_members(self, axes):
        for level in self._layout.positions:
            for individual in level:
                if individual.individual.member.generated:
                    individual_color = "grey"
                elif individual.individual.member.status == "1":
                    individual_color = "white"
                elif individual.individual.member.status == "2":
                    individual_color = "red"
                else:
                    individual_color = "purple"

                if Sex.from_name_or_value(
                        individual.individual.member.sex) == Sex.male:
                    coords = [individual.x + self._x_offset,
                              individual.y + self._y_offset]
                    axes.add_patch(mpatches.Rectangle(
                        coords, individual.size, individual.size,
                        facecolor=individual_color, edgecolor="black"))
                    cx = coords[0] + individual.size / 2.0
                    cy = coords[1] + individual.size / 2.0
                elif Sex.from_name_or_value(
                        individual.individual.member.sex) == Sex.female:
                    coords = [individual.x_center + self._x_offset,
                              individual.y_center + self._y_offset]
                    axes.add_patch(mpatches.Circle(
                        coords, old_div(individual.size, 2),
                        facecolor=individual_color, edgecolor="black"))
                    cx = coords[0]
                    cy = coords[1]
                else:
                    size = math.sqrt((individual.size ** 2) / 2)
                    coords =\
                        [individual.x + self._x_offset + (individual.size / 2),
                         individual.y + self._y_offset]
                    axes.add_patch(mpatches.Rectangle(
                        coords, size, size,
                        facecolor=individual_color, edgecolor="black",
                        angle=45.0))
                    cx = coords[0]
                    cy = coords[1] + individual.size / 2.0

                if self.show_id:
                    axes.annotate(individual.individual.member.id, (cx, cy),
                                  color='black', weight='bold', fontsize=2,
                                  ha='center', va='center')

    def _draw_family(self, axes, family):
        col_labels =\
            ["familyId", "individualId", "father", "mother", "sex", "status",
             "layout"]
        table_vals = []

        for member in family:
            table_vals.append(
                [member.family_id, member.id, member.father, member.mother,
                 member.sex, member.status, member.layout])

        axes.table = plt.table(
            cellText=table_vals, colLabels=col_labels, loc='center')

    def _horizontal_mirror_layout(self):
        highest_y = max([i.y for level in self._layout.positions
                         for i in level]) + 10

        for level in self._layout.positions:
            for individual in level:
                individual.y = highest_y - individual.y

        for line in self._layout.lines:
            line.y1 = highest_y - line.y1 + \
                self._layout.positions[0][0].size
            line.y2 = highest_y - line.y2 + \
                self._layout.positions[0][0].size
