import colorsys
from itertools import cycle

import numpy as np
import matplotlib as mpl
from matplotlib.colors import to_rgb  # type: ignore

import dae.pheno.husl as husl

"""
Copyright (c) 2012-2021, Michael L. Waskom
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the project nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


__all__ = [
    "color_palette", "blend_palette", "desaturate", "get_color_cycle",
    "dark_palette", "light_palette", "diverging_palette",
]


SEABORN_PALETTES = dict(
    deep=["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
          "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD"],
    deep6=["#4C72B0", "#55A868", "#C44E52",
           "#8172B3", "#CCB974", "#64B5CD"],
    muted=["#4878D0", "#EE854A", "#6ACC64", "#D65F5F", "#956CB4",
           "#8C613C", "#DC7EC0", "#797979", "#D5BB67", "#82C6E2"],
    muted6=["#4878D0", "#6ACC64", "#D65F5F",
            "#956CB4", "#D5BB67", "#82C6E2"],
    pastel=["#A1C9F4", "#FFB482", "#8DE5A1", "#FF9F9B", "#D0BBFF",
            "#DEBB9B", "#FAB0E4", "#CFCFCF", "#FFFEA3", "#B9F2F0"],
    pastel6=["#A1C9F4", "#8DE5A1", "#FF9F9B",
             "#D0BBFF", "#FFFEA3", "#B9F2F0"],
    bright=["#023EFF", "#FF7C00", "#1AC938", "#E8000B", "#8B2BE2",
            "#9F4800", "#F14CC1", "#A3A3A3", "#FFC400", "#00D7FF"],
    bright6=["#023EFF", "#1AC938", "#E8000B",
             "#8B2BE2", "#FFC400", "#00D7FF"],
    dark=["#001C7F", "#B1400D", "#12711C", "#8C0800", "#591E71",
          "#592F0D", "#A23582", "#3C3C3C", "#B8850A", "#006374"],
    dark6=["#001C7F", "#12711C", "#8C0800",
           "#591E71", "#B8850A", "#006374"],
    colorblind=["#0173B2", "#DE8F05", "#029E73", "#D55E00", "#CC78BC",
                "#CA9161", "#FBAFE4", "#949494", "#ECE133", "#56B4E9"],
    colorblind6=["#0173B2", "#029E73", "#D55E00",
                 "#CC78BC", "#ECE133", "#56B4E9"]
)


MPL_QUAL_PALS = {
    "tab10": 10, "tab20": 20, "tab20b": 20, "tab20c": 20,
    "Set1": 9, "Set2": 8, "Set3": 12,
    "Accent": 8, "Paired": 12,
    "Pastel1": 9, "Pastel2": 8, "Dark2": 8,
}


QUAL_PALETTE_SIZES = MPL_QUAL_PALS.copy()
QUAL_PALETTE_SIZES.update({k: len(v) for k, v in SEABORN_PALETTES.items()})
QUAL_PALETTES = list(QUAL_PALETTE_SIZES.keys())


def get_color_cycle():
    """Return the list of colors in the current matplotlib color cycle
    Parameters
    ----------
    None
    Returns
    -------
    colors : list
        List of matplotlib colors in the current cycle, or dark gray if
        the current color cycle is empty.
    """
    cycler = mpl.rcParams['axes.prop_cycle']
    return cycler.by_key()['color'] if 'color' in cycler.keys else [".15"]


class _ColorPalette(list):
    """Set the color palette in a with statement, otherwise be a list."""
    def __enter__(self):
        """Open the context."""
        from .rcmod import set_palette  # type: ignore
        self._orig_palette = color_palette()
        set_palette(self)
        return self

    def __exit__(self, *args):
        """Close the context."""
        from .rcmod import set_palette  # type: ignore
        set_palette(self._orig_palette)

    def as_hex(self):
        """Return a color palette with hex codes instead of RGB values."""
        return _ColorPalette([mpl.colors.rgb2hex(rgb) for rgb in self])

    def _repr_html_(self):
        """Rich display of the color palette in an HTML frontend."""
        s = 55
        n = len(self)
        html = f'<svg  width="{n * s}" height="{s}">'
        for i, c in enumerate(self.as_hex()):
            html += (
                f'<rect x="{i * s}" y="0" width="{s}" height="{s}" '
                f'style="fill:{c};'
                f'stroke-width:2;stroke:rgb(255,255,255)"/>'
            )
        html += '</svg>'
        return html


def desaturate(color, prop):
    """Decrease the saturation channel of a color by some percent.
    Parameters
    ----------
    color : matplotlib color
        hex, rgb-tuple, or html color name
    prop : float
        saturation channel of color will be multiplied by this value
    Returns
    -------
    new_color : rgb tuple
        desaturated color code in RGB tuple representation
    """
    # Check inputs
    if not 0 <= prop <= 1:
        raise ValueError("prop must be between 0 and 1")

    # Get rgb tuple rep
    rgb = to_rgb(color)

    # Convert to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)

    # Desaturate the saturation channel
    s *= prop

    # Convert back to rgb
    new_color = colorsys.hls_to_rgb(h, l, s)

    return new_color


def color_palette(palette=None, n_colors=None, desat=None, as_cmap=False):
    """Return a list of colors or continuous colormap defining a palette.

    Possible ``palette`` values include:
        - Name of a seaborn palette (deep, muted, bright, pastel, dark,
            colorblind)
        - Name of matplotlib colormap
        - 'husl' or 'hls'
        - 'ch:<cubehelix arguments>'
        - 'light:<color>', 'dark:<color>', 'blend:<color>,<color>',
        - A sequence of colors in any format matplotlib accepts

    Calling this function with ``palette=None`` will return the current
    matplotlib color cycle.

    This function can also be used in a ``with`` statement to temporarily
    set the color cycle for a plot or set of plots.

    See the :ref:`tutorial <palette_tutorial>` for more information.

    Parameters
    ----------
    palette : None, string, or sequence, optional
        Name of palette or None to return current palette. If a sequence, input
        colors are used but possibly cycled and desaturated.
    n_colors : int, optional
        Number of colors in the palette. If ``None``, the default will depend
        on how ``palette`` is specified. Named palettes default to 6 colors,
        but grabbing the current palette or passing in a list of colors will
        not change the number of colors unless this is specified. Asking for
        more colors than exist in the palette will cause it to cycle. Ignored
        when ``as_cmap`` is True.
    desat : float, optional
        Proportion to desaturate each color by.
    as_cmap : bool
        If True, return a :class:`matplotlib.colors.Colormap`.

    Returns
    -------
    list of RGB tuples or :class:`matplotlib.colors.Colormap`

    See Also
    --------
    set_palette : Set the default color cycle for all plots.
    set_color_codes : Reassign color codes like ``"b"``, ``"g"``, etc. to
                      colors from one of the seaborn palettes.

    Examples
    --------

    .. include:: ../docstrings/color_palette.rst

    """
    if palette is None:
        palette = get_color_cycle()
        if n_colors is None:
            n_colors = len(palette)

    elif not isinstance(palette, str):
        if n_colors is None:
            n_colors = len(palette)
    else:
        raise ValueError("String palettes not supported")

    if desat is not None:
        palette = [desaturate(c, desat) for c in palette]

    if not as_cmap:

        # Always return as many colors as we asked for
        pal_cycle = cycle(palette)
        palette = [next(pal_cycle) for _ in range(n_colors)]

        # Always return in r, g, b tuple format
        try:
            palette = map(mpl.colors.colorConverter.to_rgb, palette)
            palette = _ColorPalette(palette)
        except ValueError:
            raise ValueError(f"Could not generate a palette for {palette}")

    return palette


def _color_to_rgb(color, input):
    """Add some more flexibility to color choices."""
    if input == "hls":
        color = colorsys.hls_to_rgb(*color)
    elif input == "husl":
        color = husl.husl_to_rgb(*color)
        color = tuple(np.clip(color, 0, 1))

    return mpl.colors.to_rgb(color)


def blend_palette(colors, n_colors=6, as_cmap=False, input="rgb"):
    """Make a palette that blends between a list of colors.

    Parameters
    ----------
    colors : sequence of colors in various formats interpreted by ``input``
        hex code, html color name, or tuple in ``input`` space.
    n_colors : int, optional
        Number of colors in the palette.
    as_cmap : bool, optional
        If True, return a :class:`matplotlib.colors.Colormap`.

    Returns
    -------
    list of RGB tuples or :class:`matplotlib.colors.Colormap`

    """
    colors = [_color_to_rgb(color, input) for color in colors]
    name = "blend"
    pal = mpl.colors.LinearSegmentedColormap.from_list(name, colors)
    if not as_cmap:
        rgb_array = pal(np.linspace(0, 1, int(n_colors)))[:, :3]  # no alpha
        pal = _ColorPalette(map(tuple, rgb_array))
    return pal


def dark_palette(color, n_colors=6, reverse=False, as_cmap=False, input="rgb"):
    """Make a sequential palette that blends from dark to ``color``.

    This kind of palette is good for data that range between relatively
    uninteresting low values and interesting high values.

    The ``color`` parameter can be specified in a number of ways, including
    all options for defining a color in matplotlib and several additional
    color spaces that are handled by seaborn. You can also use the database
    of named colors from the XKCD color survey.

    If you are using the IPython notebook, you can also choose this palette
    interactively with the :func:`choose_dark_palette` function.

    Parameters
    ----------
    color : base color for high values
        hex, rgb-tuple, or html color name
    n_colors : int, optional
        number of colors in the palette
    reverse : bool, optional
        if True, reverse the direction of the blend
    as_cmap : bool, optional
        If True, return a :class:`matplotlib.colors.Colormap`.
    input : {'rgb', 'hls', 'husl', xkcd'}
        Color space to interpret the input color. The first three options
        apply to tuple inputs and the latter applies to string inputs.

    Returns
    -------
    list of RGB tuples or :class:`matplotlib.colors.Colormap`

    See Also
    --------
    light_palette : Create a sequential palette with bright low values.
    diverging_palette : Create a diverging palette with two colors.

    Examples
    --------

    Generate a palette from an HTML color:

    .. plot::
        :context: close-figs

        >>> import seaborn as sns; sns.set_theme()
        >>> sns.palplot(sns.dark_palette("purple"))

    Generate a palette that decreases in lightness:

    .. plot::
        :context: close-figs

        >>> sns.palplot(sns.dark_palette("seagreen", reverse=True))

    Generate a palette from an HUSL-space seed:

    .. plot::
        :context: close-figs

        >>> sns.palplot(sns.dark_palette((260, 75, 60), input="husl"))

    Generate a colormap object:

    .. plot::
        :context: close-figs

        >>> from numpy import arange
        >>> x = arange(25).reshape(5, 5)
        >>> cmap = sns.dark_palette("#2ecc71", as_cmap=True)
        >>> ax = sns.heatmap(x, cmap=cmap)

    """
    rgb = _color_to_rgb(color, input)
    h, s, _l = husl.rgb_to_husl(*rgb)
    gray_s, gray_l = .15 * s, 15
    gray = _color_to_rgb((h, gray_s, gray_l), input="husl")
    colors = [rgb, gray] if reverse else [gray, rgb]
    return blend_palette(colors, n_colors, as_cmap)


def light_palette(
        color, n_colors=6, reverse=False, as_cmap=False, input="rgb"):
    """Make a sequential palette that blends from light to ``color``.

    This kind of palette is good for data that range between relatively
    uninteresting low values and interesting high values.

    The ``color`` parameter can be specified in a number of ways, including
    all options for defining a color in matplotlib and several additional
    color spaces that are handled by seaborn. You can also use the database
    of named colors from the XKCD color survey.

    If you are using the IPython notebook, you can also choose this palette
    interactively with the :func:`choose_light_palette` function.

    Parameters
    ----------
    color : base color for high values
        hex code, html color name, or tuple in ``input`` space.
    n_colors : int, optional
        number of colors in the palette
    reverse : bool, optional
        if True, reverse the direction of the blend
    as_cmap : bool, optional
        If True, return a :class:`matplotlib.colors.Colormap`.
    input : {'rgb', 'hls', 'husl', xkcd'}
        Color space to interpret the input color. The first three options
        apply to tuple inputs and the latter applies to string inputs.

    Returns
    -------
    list of RGB tuples or :class:`matplotlib.colors.Colormap`

    See Also
    --------
    dark_palette : Create a sequential palette with dark low values.
    diverging_palette : Create a diverging palette with two colors.

    Examples
    --------

    Generate a palette from an HTML color:

    .. plot::
        :context: close-figs

        >>> import seaborn as sns; sns.set_theme()
        >>> sns.palplot(sns.light_palette("purple"))

    Generate a palette that increases in lightness:

    .. plot::
        :context: close-figs

        >>> sns.palplot(sns.light_palette("seagreen", reverse=True))

    Generate a palette from an HUSL-space seed:

    .. plot::
        :context: close-figs

        >>> sns.palplot(sns.light_palette((260, 75, 60), input="husl"))

    Generate a colormap object:

    .. plot::
        :context: close-figs

        >>> from numpy import arange
        >>> x = arange(25).reshape(5, 5)
        >>> cmap = sns.light_palette("#2ecc71", as_cmap=True)
        >>> ax = sns.heatmap(x, cmap=cmap)

    """
    rgb = _color_to_rgb(color, input)
    h, s, _l = husl.rgb_to_husl(*rgb)
    gray_s, gray_l = .15 * s, 95
    gray = _color_to_rgb((h, gray_s, gray_l), input="husl")
    colors = [rgb, gray] if reverse else [gray, rgb]
    return blend_palette(colors, n_colors, as_cmap)


def diverging_palette(h_neg, h_pos, s=75, l=50, sep=1, n=6,  # noqa
                      center="light", as_cmap=False):
    """Make a diverging palette between two HUSL colors.

    If you are using the IPython notebook, you can also choose this palette
    interactively with the :func:`choose_diverging_palette` function.

    Parameters
    ----------
    h_neg, h_pos : float in [0, 359]
        Anchor hues for negative and positive extents of the map.
    s : float in [0, 100], optional
        Anchor saturation for both extents of the map.
    l : float in [0, 100], optional
        Anchor lightness for both extents of the map.
    sep : int, optional
        Size of the intermediate region.
    n : int, optional
        Number of colors in the palette (if not returning a cmap)
    center : {"light", "dark"}, optional
        Whether the center of the palette is light or dark
    as_cmap : bool, optional
        If True, return a :class:`matplotlib.colors.Colormap`.

    Returns
    -------
    list of RGB tuples or :class:`matplotlib.colors.Colormap`

    See Also
    --------
    dark_palette : Create a sequential palette with dark values.
    light_palette : Create a sequential palette with light values.

    Examples
    --------

    Generate a blue-white-red palette:

    .. plot::
        :context: close-figs

        >>> import seaborn as sns; sns.set_theme()
        >>> sns.palplot(sns.diverging_palette(240, 10, n=9))

    Generate a brighter green-white-purple palette:

    .. plot::
        :context: close-figs

        >>> sns.palplot(sns.diverging_palette(150, 275, s=80, l=55, n=9))

    Generate a blue-black-red palette:

    .. plot::
        :context: close-figs

        >>> sns.palplot(sns.diverging_palette(250, 15, s=75, l=40,
        ...                                   n=9, center="dark"))

    Generate a colormap object:

    .. plot::
        :context: close-figs

        >>> from numpy import arange
        >>> x = arange(25).reshape(5, 5)
        >>> cmap = sns.diverging_palette(220, 20, as_cmap=True)
        >>> ax = sns.heatmap(x, cmap=cmap)

    """
    palfunc = dict(dark=dark_palette, light=light_palette)[center]
    n_half = int(128 - (sep // 2))
    neg = palfunc((h_neg, s, l), n_half, reverse=True, input="husl")
    pos = palfunc((h_pos, s, l), n_half, input="husl")
    midpoint = dict(light=[(.95, .95, .95)], dark=[(.133, .133, .133)])[center]
    mid = midpoint * sep
    pal = blend_palette(np.concatenate([neg, mid, pos]), n, as_cmap=as_cmap)
    return pal
