"""Classes and helpers for drawing pedigrees into a PDF file."""

import math
from copy import deepcopy
from typing import List

import matplotlib as mpl
import matplotlib.pyplot as plt

import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.path import Path
from matplotlib.backends.backend_pdf import PdfPages

from dae.variants.attributes import Sex, Role, Status
from dae.pedigrees.layout import Layout, Point


mpl.use("PS")  # noqa
plt.ioff()  # noqa


class PDFLayoutDrawer:
    """Helper class for producing PDF file with multiple pedigrees."""

    def __init__(self, filename):
        self._filename = filename
        self._pages = []
        self.pdf = None

    def __enter__(self):
        self.pdf = PdfPages(self._filename)
        return self.pdf

    def add_page(self, figure, title=None):
        if title:
            figure.text(0.5, 0.9, title, horizontalalignment="center")
        self.pdf.savefig(figure)
        plt.close(figure)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.pdf.close()


class OffsetLayoutDrawer:
    """Class drawing a family pedigree using a prebuild family layout."""

    # pylint: disable=too-few-public-methods
    GAP = 2.0

    def __init__(
            self,
            layouts: List[Layout],
            x_offset=0,
            y_offset=0,
            show_family=False):

        assert layouts is not None

        self._x_offset = x_offset
        self._y_offset = y_offset
        self._gap = self.GAP
        self._layouts = deepcopy(layouts)
        self._layouts_vertical_inverse()
        # for layout in self._layouts:
        #     layout.scale(0.5)

        self.show_family = show_family
        self.figsize = (7, 10)

    def _layouts_vertical_inverse(self):
        highest_y = max(
            max([i.y for level in layout.positions for i in level]) + 10
            for layout in self._layouts
        )

        for layout in self._layouts:
            for level in layout.positions:
                for individual in level:
                    individual.y = highest_y - individual.y

            for line in layout.lines:
                line.y1 = highest_y - line.y1 + layout.positions[0][0].size
                line.y2 = highest_y - line.y2 + layout.positions[0][0].size

    def draw(self, figure=None, title=None, tags=None):
        """Draw family pedigree."""
        if figure is None:
            figure = plt.figure(figsize=self.figsize)

        pedigree_axes_rect = (0.1, 0.3, 0.8, 0.6)
        if self.show_family:
            pedigree_axes_rect = (0.1, 0.35, 0.8, 0.55)

        ax_pedigree = figure.add_axes(pedigree_axes_rect)
        ax_pedigree.axis("off")
        ax_pedigree.set_aspect(
            aspect="equal", adjustable="datalim", anchor="C"
        )
        ax_pedigree.autoscale_view()

        for layout in self._layouts:
            self._draw_lines(ax_pedigree, layout)
            self._draw_rounded_lines(ax_pedigree, layout)

            self._draw_members(ax_pedigree, layout)
        if tags:
            tags = "\n".join(sorted(tags))
            props = {"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5}
            ax_pedigree.text(
                0.99, 0.01, tags,
                transform=ax_pedigree.transAxes,
                fontsize=5,
                verticalalignment="bottom",
                horizontalalignment="right",
                bbox=props)

        ax_pedigree.plot()

        if self.show_family:
            ax_family = figure.add_axes((0.1, 0.1, 0.8, 0.3))
            ax_family.axis("off")
            ax_family.set_aspect(
                aspect="equal", adjustable="datalim", anchor="C"
            )
            ax_family.autoscale_view()

            family = [
                member.individual.member
                for layout in self._layouts
                for layer in layout.positions
                for member in layer
            ]

            self._draw_family_table(ax_family, family)

            ax_family.plot()

        if title:
            self._draw_title(figure, title)

        return figure

    def _draw_lines(self, axes, layout):
        for line in layout.lines:
            if not line.curved:
                axes.add_line(
                    mlines.Line2D(
                        [line.x1 + self._x_offset, line.x2 + self._x_offset],
                        [line.y1 + self._y_offset, line.y2 + self._y_offset],
                        color="black",
                    )
                )

    def _draw_rounded_lines(self, axes, layout):
        def elementwise_sum(x_pos, y_pos):
            return tuple([x_pos[0] + y_pos[0], x_pos[1] + y_pos[1]])
        for line in layout.lines:
            if line.curved:
                offset = (self._x_offset, self._y_offset)
                verts = [
                    elementwise_sum(line.curve_p0(), offset),
                    elementwise_sum(line.curve_p1(), offset),
                    elementwise_sum(line.curve_p2(), offset),
                    elementwise_sum(line.curve_p3(), offset),
                ]

                codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]

                path = Path(verts, codes)

                axes.add_patch(mpatches.PathPatch(path, facecolor="none"))

    @staticmethod
    def _infer_individual_color(individual) -> str:
        if individual.individual.member.generated or \
                individual.individual.member.not_sequenced:
            return "grey"
        if individual.individual.member.status == Status.unaffected:
            return "white"
        if individual.individual.member.status == Status.affected:
            return "red"
        return "purple"

    def _draw_male_individual(self, axes, individual, color):
        coords = [
            individual.x + self._x_offset,
            individual.y + self._y_offset,
        ]
        axes.add_patch(
            mpatches.Rectangle(
                coords,
                individual.size,
                individual.size,
                facecolor=color,
                edgecolor="black",
            )
        )

        center_x = coords[0] + individual.size / 2.0
        center_y = coords[1] + individual.size / 2.0

        dlx = coords[0]
        dly = coords[1]

        return Point(center_x, center_y), Point(dlx, dly)

    def _draw_female_individual(self, axes, individual, color):
        coords = [
            individual.x_center + self._x_offset,
            individual.y_center + self._y_offset,
        ]
        axes.add_patch(
            mpatches.Circle(
                coords,
                individual.size / 2,
                facecolor=color,
                edgecolor="black",
            )
        )

        center_x = coords[0]
        center_y = coords[1]

        dlx = coords[0] + (individual.size / 2.0) * math.cos(
            math.radians(225)
        )
        dly = coords[1] + (individual.size / 2.0) * math.sin(
            math.radians(225)
        )
        return Point(center_x, center_y), Point(dlx, dly)

    def _draw_unspecified_sex_individual(self, axes, individual, color):
        size = math.sqrt((individual.size ** 2) / 2)
        coords = [
            individual.x + self._x_offset + (individual.size / 2),
            individual.y + self._y_offset,
        ]
        axes.add_patch(
            mpatches.Rectangle(
                coords,
                size,
                size,
                facecolor=color,
                edgecolor="black",
                angle=45.0,
            )
        )

        center_x = coords[0]
        center_y = coords[1] + individual.size / 2.0

        dlx = coords[0] - individual.size / 4
        dly = coords[1] + individual.size / 4

        return Point(center_x, center_y), Point(dlx, dly)

    def _draw_individual(self, axes, individual):
        individual_color = self._infer_individual_color(individual)

        if Sex.from_name(individual.individual.member.sex) == Sex.male:
            center, bottom_left = self._draw_male_individual(
                axes, individual, individual_color)
        elif Sex.from_name(individual.individual.member.sex) == Sex.female:
            center, bottom_left = self._draw_female_individual(
                axes, individual, individual_color)

        else:
            center, bottom_left = self._draw_unspecified_sex_individual(
                axes, individual, individual_color)

        if individual.individual.member.role == Role.prb:
            axes.add_patch(
                mpatches.FancyArrow(
                    bottom_left.x - self._gap,
                    bottom_left.y - self._gap,
                    self._gap,
                    self._gap,
                    length_includes_head=True,
                    color="black",
                    head_width=1.0,
                    linewidth=0.1,
                )
            )

        axes.annotate(
            individual.individual.member.person_id,
            (center.x, center.y),
            color="black",
            weight="bold",
            fontsize=5,
            ha="center",
            va="center",
        )

    def _draw_members(self, axes, layout):
        for level in layout.positions:
            for individual in level:
                self._draw_individual(axes, individual)

    @staticmethod
    def _draw_family_table(axes, family):
        col_labels = [
            "familyId",
            "individualId",
            "father",
            "mother",
            "sex",
            "status",
            "role",
            "layout",
            "generated",
            "not_sequenced",
        ]
        table_vals = []

        for member in family:
            table_vals.append(
                [
                    member.family_id,
                    member.person_id,
                    member.dad_id,
                    member.mom_id,
                    Sex.from_name(member.sex),
                    member.status,
                    member.role,
                    member.layout,
                    "G" if member.generated else "",
                    "N" if member.not_sequenced else "",
                ]
            )

        axes.table = plt.table(
            cellText=table_vals, colLabels=col_labels, loc="center"
        )

    @staticmethod
    def _draw_title(figure, title, x_pos=0.5, y_pos=0.9, **kwargs):
        figure.text(
            x_pos, y_pos, title, horizontalalignment="center", **kwargs)
