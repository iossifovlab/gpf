from copy import deepcopy
import math
from itertools import zip_longest

import matplotlib as mpl
import matplotlib.pyplot as plt

import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.path import Path
from matplotlib.backends.backend_pdf import PdfPages

from dae.variants.attributes import Sex, Role, Status


mpl.use("PS")  # noqa
plt.ioff()  # noqa


class PDFLayoutDrawer(object):
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


class OffsetLayoutDrawer(object):
    def __init__(
            self,
            layout,
            x_offset,
            y_offset,
            gap=4.0,
            show_id=False,
            show_family=False,
            figsize=(7, 10)):

        assert layout is not None

        self._x_offset = x_offset
        self._y_offset = y_offset
        self._gap = gap
        self._layout = deepcopy(layout)
        self.show_id = show_id
        self.show_family = show_family
        self.figsize = figsize
        if self._layout is not None:
            self._horizontal_mirror_layout()

    def draw(self, figure=None, ax=None, title=None, tags=None):
        if figure is None:
            figure = plt.figure(figsize=self.figsize)

        if ax is not None:
            ax_pedigree = ax

        else:
            pedigree_axes_rect = (0.1, 0.3, 0.8, 0.6)
            if self.show_family:
                pedigree_axes_rect = (0.1, 0.35, 0.8, 0.55)

            ax_pedigree = figure.add_axes(pedigree_axes_rect)
            ax_pedigree.axis("off")
            ax_pedigree.set_aspect(
                aspect="equal", adjustable="datalim", anchor="C"
            )
            ax_pedigree.autoscale_view()
        for layout in self._layout:
            self._draw_lines(ax_pedigree, layout)
            self._draw_rounded_lines(ax_pedigree, layout)

            self._draw_members(ax_pedigree, layout)
        if tags:
            tags = "\n".join(sorted(tags))
            props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
            ax_pedigree.text(
                0.99, 0.01, tags,
                transform=ax_pedigree.transAxes,
                fontsize=5,
                verticalalignment="bottom",
                horizontalalignment="right",
                bbox=props)

        if ax:
            return ax_pedigree

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
                for layout in self._layout
                for layer in layout.positions
                for member in layer
            ]

            self._draw_family(ax_family, family)

            ax_family.plot()

        if title:
            self._draw_title(figure, title)

        return figure

    def draw_family_table(self, family, figure=None, ax=None, title=None):
        if figure is None:
            figure = plt.figure(figsize=self.figsize)

        ax_family = figure.add_axes((0.1, 0.1, 0.8, 0.3))
        ax_family.axis("off")
        ax_family.set_aspect(aspect="equal", adjustable="datalim", anchor="C")
        ax_family.autoscale_view()

        self._draw_family(ax_family, family.full_members)

        ax_family.plot()

        if title:
            self._draw_title(figure, title)

        return figure

    def draw_family(self, family, title=None):
        figure, ax = plt.subplots(figsize=self.figsize)
        ax.axis("off")

        self._draw_family(figure, family)

        if title:
            self._draw_title(figure, title)

        return figure

    def draw_families_report(self, families_report, layout):
        people_counters = self.draw_people_counters(families_report)
        families_counters = self.draw_families_counters(
            families_report, layout
        )

        return people_counters + families_counters

    def draw_people_counters(self, families_report):
        pcf = []
        for people_counter in families_report.people_counters:
            figure, ax = plt.subplots(figsize=self.figsize)
            ax.axis("off")

            table_vals = [
                [people_counter.group_name],
                ["People Male"],
                ["People Female"],
                ["People Unspecified"],
                ["People Total"],
            ]

            for phenotype in people_counter.counters:
                table_vals[0].append(phenotype.column)
                table_vals[1].append(phenotype.people_male)
                table_vals[2].append(phenotype.people_female)
                table_vals[3].append(phenotype.people_unspecified)
                table_vals[4].append(phenotype.people_total)

            ax.table = plt.table(
                cellText=table_vals[1:], colLabels=table_vals[0], loc="center"
            )

            ax.plot()

            figure.text(
                0.1,
                0.7,
                "Total number of families: "
                + str(families_report.families_total),
                horizontalalignment="left",
            )

            self._draw_title(figure, "People counters")

            pcf.append(figure)

        return pcf

    def draw_families_counters(self, families_report, layout):
        fcf = []
        families_counters = [
            counter
            for fc in families_report.families_counters
            for c in fc.counters
            for counter in c.counters
        ]
        for families in zip_longest(*(iter(families_counters),) * 9):
            figure, ax = plt.subplots(3, 3, figsize=self.figsize)

            for row, families_row in enumerate(
                zip_longest(*(iter(families),) * 3)
            ):
                for col, family in enumerate(families_row):
                    ax[row][col].axis("off")
                    ax[row][col].set_aspect(
                        aspect="equal", adjustable="datalim", anchor="C"
                    )
                    ax[row][col].autoscale_view()

                    if family is None:
                        continue
                    family_layout = layout[family.pedigree[0][0]]

                    if family_layout is None:
                        self._draw_title(
                            ax[row][col],
                            "Invalid coordinates",
                            x=0.5,
                            y=1.1,
                            fontsize=6,
                            transform=ax[row][col].transAxes,
                        )
                    else:
                        layout_drawer = OffsetLayoutDrawer(family_layout, 0, 0)
                        layout_drawer.draw(ax=ax[row][col])
                        self._draw_title(
                            ax[row][col],
                            "Pedigrees Count: " + str(family.pedigrees_count),
                            x=0.5,
                            y=1.1,
                            fontsize=6,
                            transform=ax[row][col].transAxes,
                        )

                    ax[row][col].plot()

            self._draw_title(figure, "Families counters", x=0.5, y=0.95)

            fcf.append(figure)

        return fcf

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
        def elementwise_sum(x, y):
            return tuple([x[0] + y[0], x[1] + y[1]])
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

            # line = ()

    def _draw_members(self, axes, layout):
        for level in layout.positions:
            for individual in level:
                if individual.individual.member.generated or \
                        individual.individual.member.not_sequenced:
                    individual_color = "grey"
                elif individual.individual.member.status == Status.unaffected:
                    individual_color = "white"
                elif individual.individual.member.status == Status.affected:
                    individual_color = "red"
                else:
                    individual_color = "purple"

                if Sex.from_name(individual.individual.member.sex) == Sex.male:
                    coords = [
                        individual.x + self._x_offset,
                        individual.y + self._y_offset,
                    ]
                    axes.add_patch(
                        mpatches.Rectangle(
                            coords,
                            individual.size,
                            individual.size,
                            facecolor=individual_color,
                            edgecolor="black",
                        )
                    )

                    cx = coords[0] + individual.size / 2.0
                    cy = coords[1] + individual.size / 2.0

                    dlx = coords[0]
                    dly = coords[1]
                elif (
                    Sex.from_name(individual.individual.member.sex)
                    == Sex.female
                ):
                    coords = [
                        individual.x_center + self._x_offset,
                        individual.y_center + self._y_offset,
                    ]
                    axes.add_patch(
                        mpatches.Circle(
                            coords,
                            individual.size / 2,
                            facecolor=individual_color,
                            edgecolor="black",
                        )
                    )

                    cx = coords[0]
                    cy = coords[1]

                    dlx = coords[0] + (individual.size / 2.0) * math.cos(
                        math.radians(225)
                    )
                    dly = coords[1] + (individual.size / 2.0) * math.sin(
                        math.radians(225)
                    )
                else:
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
                            facecolor=individual_color,
                            edgecolor="black",
                            angle=45.0,
                        )
                    )

                    cx = coords[0]
                    cy = coords[1] + individual.size / 2.0

                    dlx = coords[0] - individual.size / 4
                    dly = coords[1] + individual.size / 4

                if individual.individual.member.role == Role.prb:
                    axes.add_patch(
                        mpatches.FancyArrow(
                            dlx - self._gap,
                            dly - self._gap,
                            self._gap,
                            self._gap,
                            length_includes_head=True,
                            color="black",
                            head_width=2.0,
                            linewidth=0.1,
                        )
                    )

                if self.show_id:
                    axes.annotate(
                        individual.individual.member.person_id,
                        (cx, cy),
                        color="black",
                        weight="bold",
                        fontsize=5,
                        ha="center",
                        va="center",
                    )

    def _draw_family(self, axes, family):
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

    def _draw_title(self, figure, title, x=0.5, y=0.9, **kwargs):
        figure.text(x, y, title, horizontalalignment="center", **kwargs)

    def _horizontal_mirror_layout(self):
        highest_y = max(
            max([i.y for level in layout.positions for i in level]) + 10
            for layout in self._layout
        )

        for layout in self._layout:
            for level in layout.positions:
                for individual in level:
                    individual.y = highest_y - individual.y

            for line in layout.lines:
                line.y1 = highest_y - line.y1 + layout.positions[0][0].size
                line.y2 = highest_y - line.y2 + layout.positions[0][0].size
