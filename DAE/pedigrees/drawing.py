from copy import deepcopy

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.backends.backend_pdf import PdfPages


class PDFLayoutDrawer(object):

    def __init__(self, filename):
        self._filename = filename
        self._pages = []

    def add_page(self, figure):
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

        figure.lines += self._draw_lines()

        figure.patches += self._draw_members()

        return figure

    def _draw_lines(self):
        result = []

        for line in self._layout.lines:
            result.append(mlines.Line2D(
                [line.x1 + self._x_offset, line.x2 + self._x_offset],
                [line.y1 + self._y_offset, line.y2 + self._y_offset],
                color="black"
            ))

        return result

    def _draw_members(self):
        result = []

        for level in self._layout.positions:
            for individual in level:
                if individual.individual.member.sex == '1':
                    coords = [individual.x_center + self._x_offset,
                              individual.y_center + self._y_offset]
                    result.append(mpatches.Circle(
                        coords, individual.size / 2,
                        facecolor="white", edgecolor="black"))
                else:
                    coords = [individual.x + self._x_offset,
                              individual.y + self._y_offset]
                    result.append(mpatches.Rectangle(
                                  coords, individual.size, individual.size,
                                  facecolor="white", edgecolor="black"))

        return result

    def _horizontal_mirror_layout(self):
        highest_y = max([i.y for level in self._layout.positions
                         for i in level]) + 10
        highest_y_line = max([line.y1 for line in self._layout.lines] +
                             [line.y2 for line in self._layout.lines]) + 10

        for level in self._layout.positions:
            for individual in level:
                individual.y = highest_y - individual.y

        for line in self._layout.lines:
            line.y1 = highest_y_line - line.y1 + \
                self._layout.positions[0][0].size
            line.y2 = highest_y_line - line.y2 + \
                self._layout.positions[0][0].size
