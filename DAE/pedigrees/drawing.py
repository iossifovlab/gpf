from copy import deepcopy

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.backends.backend_pdf import PdfPages


class PDFLayoutDrawer(object):

    def __init__(self, filename):
        self._filename = filename
        self._pages = []

    def add_page(self, layout):
        layout = deepcopy(layout)
        self._horizontal_mirror_layout(layout)
        figure = self._draw(layout)
        self._pages.append(figure)

    def save_file(self):
        with PdfPages(self._filename) as pdf:
            for page in self._pages:
                pdf.savefig(page)
                # page.close()

    def _draw(self, layout):
        figure = plt.figure()

        for line in layout.lines:
            figure.lines.append(mlines.Line2D(
                [line.x1, line.x2], [line.y1, line.y2], color="black"
            ))

        for level in layout.positions:
            for individual in level:
                figure.patches.append(
                    self._figure_from_member(individual)
                )

        return figure

    def _figure_from_member(self, individual):
        if individual.individual.member.sex == '1':
            return mpatches.Circle([individual.x_center, individual.y_center],
                                   individual.size / 2,
                                   facecolor="white", edgecolor="black")
        return mpatches.Rectangle([individual.x, individual.y],
                                  individual.size, individual.size,
                                  facecolor="white", edgecolor="black")

    def _horizontal_mirror_layout(self, layout):
        highest_y = max([i.y for level in layout.positions
                         for i in level]) + 10
        highest_y_line = max([line.y1 for line in layout.lines] +
                             [line.y2 for line in layout.lines]) + 10

        for level in layout.positions:
            for individual in level:
                individual.y = highest_y - individual.y

        for line in layout.lines:
            line.y1 = highest_y_line - line.y1 + \
                layout.positions[0][0].size
            line.y2 = highest_y_line - line.y2 + \
                layout.positions[0][0].size

    def _scale(self):
        pass
        # max_xy = max(
        #     max([i.y for level in self.layout.positions for i in level]),
        #     max([i.x for level in self.layout.positions for i in level]),
        # )
        #
        # for level in self.layout.positions:
        #     for individual in level:
        #         individual.x /= max_xy
        #         individual.y /= max_xy
        #
        # for line in self.layout.lines:
        #     line.x1 /= max_xy
        #     line.x2 /= max_xy
        #     line.y1 /= max_xy
        #     line.y2 /= max_xy
