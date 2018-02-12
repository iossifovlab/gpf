from copy import deepcopy

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.path import Path
from matplotlib.backends.backend_pdf import PdfPages


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


class OffsetLayoutDrawer(object):

    def __init__(self, layout, x_offset, y_offset):
        self._x_offset = x_offset
        self._y_offset = y_offset
        self._layout = deepcopy(layout)
        self._horizontal_mirror_layout()

    def draw(self, figure=None):
        if figure is None:
            figure = plt.figure()

        self._draw_lines(figure)
        self._draw_rounded_lines(figure)

        self._draw_members(figure)

        return figure

    def _draw_lines(self, figure):
        lines = []

        for line in self._layout.lines:
            if not line.curved:
                lines.append(mlines.Line2D(
                    [line.x1 + self._x_offset, line.x2 + self._x_offset],
                    [line.y1 + self._y_offset, line.y2 + self._y_offset],
                    color="black"
                ))

        figure.lines += lines

    def _draw_rounded_lines(self, figure):
        patches = []
        lines = []

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

                patches.append(
                    mpatches.PathPatch(path, facecolor='none')
                )

                # line = ()

        figure.lines += lines
        figure.patches += patches

    def _draw_members(self, figure):
        patches = []

        for level in self._layout.positions:
            for individual in level:
                if individual.individual.member.sex == '1':
                    coords = [individual.x_center + self._x_offset,
                              individual.y_center + self._y_offset]
                    patches.append(mpatches.Circle(
                        coords, individual.size / 2,
                        facecolor="white", edgecolor="black"))
                else:
                    coords = [individual.x + self._x_offset,
                              individual.y + self._y_offset]
                    patches.append(mpatches.Rectangle(
                                  coords, individual.size, individual.size,
                                  facecolor="white", edgecolor="black"))

        figure.patches += patches

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
