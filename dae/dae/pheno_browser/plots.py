import warnings
import itertools
from colorsys import rgb_to_hls
from functools import partial
from inspect import signature
from copy import copy
from collections import UserString
from collections.abc import Iterable, Sequence, Mapping
from numbers import Number
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.cbook import normalize_kwargs

from dae.pheno_browser.palletes import \
    color_palette, husl_palette, light_palette, \
    dark_palette, get_color_cycle, QUAL_PALETTES


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
    "stripplot", "violinplot"
]


def _check_argument(param, options, value):
    """Raise if value for param is not in options."""
    if value not in options:
        raise ValueError(
            f"`{param}` must be one of {options}, but {repr(value)} was passed."
        )


def share_init_params_with_map(cls):
    """Make cls.map a classmethod with same signature as cls.__init__."""
    map_sig = signature(cls.map)
    init_sig = signature(cls.__init__)

    new = [v for k, v in init_sig.parameters.items() if k != "self"]
    new.insert(0, map_sig.parameters["cls"])
    cls.map.__signature__ = map_sig.replace(parameters=new)
    cls.map.__doc__ = cls.__init__.__doc__

    cls.map = classmethod(cls.map)

    return cls


class SemanticMapping:
    """Base class for mapping data values to plot attributes."""

    # -- Default attributes that all SemanticMapping subclasses must set

    # Whether the mapping is numeric, categorical, or datetime
    map_type = None

    # Ordered list of unique values in the input data
    levels = None

    # A mapping from the data values to corresponding plot attributes
    lookup_table = None

    def __init__(self, plotter):

        # TODO Putting this here so we can continue to use a lot of the
        # logic that's built into the library, but the idea of this class
        # is to move towards semantic mappings that are agnostic about the
        # kind of plot they're going to be used to draw.
        # Fully achieving that is going to take some thinking.
        self.plotter = plotter

    def map(cls, plotter, *args, **kwargs):
        # This method is assigned the __init__ docstring
        method_name = "_{}_map".format(cls.__name__[:-7].lower())
        setattr(plotter, method_name, cls(plotter, *args, **kwargs))
        return plotter

    def _lookup_single(self, key):
        """Apply the mapping to a single data value."""
        return self.lookup_table[key]

    def __call__(self, key, *args, **kwargs):
        """Get the attribute(s) values for the data key."""
        if isinstance(key, (list, np.ndarray, pd.Series)):
            return [self._lookup_single(k, *args, **kwargs) for k in key]
        else:
            return self._lookup_single(key, *args, **kwargs)


@share_init_params_with_map
class HueMapping(SemanticMapping):
    """Mapping that sets artist colors according to data values."""
    # A specification of the colors that should appear in the plot
    palette = None

    # An object that normalizes data values to [0, 1] range for color mapping
    norm = None

    # A continuous colormap object for interpolating in a numeric context
    cmap = None

    def __init__(
        self, plotter, palette=None, order=None, norm=None,
    ):
        """Map the levels of the `hue` variable to distinct colors.

        Parameters
        ----------
        # TODO add generic parameters

        """
        super().__init__(plotter)

        data = plotter.plot_data.get("hue", pd.Series(dtype=float))

        if data.notna().any():

            map_type = self.infer_map_type(
                palette, norm, plotter.input_format, plotter.var_types["hue"]
            )

            # Our goal is to end up with a dictionary mapping every unique
            # value in `data` to a color. We will also keep track of the
            # metadata about this mapping we will need for, e.g., a legend

            # --- Option 1: numeric mapping with a matplotlib colormap

            if map_type == "numeric":

                data = pd.to_numeric(data)
                levels, lookup_table, norm, cmap = self.numeric_mapping(
                    data, palette, norm,
                )

            # --- Option 2: categorical mapping using seaborn palette

            elif map_type == "categorical":

                cmap = norm = None
                levels, lookup_table = self.categorical_mapping(
                    data, palette, order,
                )

            # --- Option 3: datetime mapping

            else:
                # TODO this needs actual implementation
                cmap = norm = None
                levels, lookup_table = self.categorical_mapping(
                    # Casting data to list to handle differences in the way
                    # pandas and numpy represent datetime64 data
                    list(data), palette, order,
                )

            self.map_type = map_type
            self.lookup_table = lookup_table
            self.palette = palette
            self.levels = levels
            self.norm = norm
            self.cmap = cmap

    def _lookup_single(self, key):
        """Get the color for a single value, using colormap to interpolate."""
        try:
            # Use a value that's in the original data vector
            value = self.lookup_table[key]
        except KeyError:
            # Use the colormap to interpolate between existing datapoints
            # (e.g. in the context of making a continuous legend)
            try:
                normed = self.norm(key)
            except TypeError as err:
                if np.isnan(key):
                    value = (0, 0, 0, 0)
                else:
                    raise err
            else:
                if np.ma.is_masked(normed):
                    normed = np.nan
                value = self.cmap(normed)
        return value

    def infer_map_type(self, palette, norm, input_format, var_type):
        """Determine how to implement the mapping."""
        if palette in QUAL_PALETTES:
            map_type = "categorical"
        elif norm is not None:
            map_type = "numeric"
        elif isinstance(palette, (dict, list)):
            map_type = "categorical"
        elif input_format == "wide":
            map_type = "categorical"
        else:
            map_type = var_type

        return map_type

    def categorical_mapping(self, data, palette, order):
        """Determine colors when the hue mapping is categorical."""
        # -- Identify the order and name of the levels

        levels = categorical_order(data, order)
        n_colors = len(levels)

        # -- Identify the set of colors to use

        if isinstance(palette, dict):

            missing = set(levels) - set(palette)
            if any(missing):
                err = "The palette dictionary is missing keys: {}"
                raise ValueError(err.format(missing))

            lookup_table = palette

        else:

            if palette is None:
                if n_colors <= len(get_color_cycle()):
                    colors = color_palette(None, n_colors)
                else:
                    colors = color_palette("husl", n_colors)
            elif isinstance(palette, list):
                if len(palette) != n_colors:
                    err = "The palette list has the wrong number of colors."
                    raise ValueError(err)
                colors = palette
            else:
                colors = color_palette(palette, n_colors)

            lookup_table = dict(zip(levels, colors))

        return levels, lookup_table

    def numeric_mapping(self, data, palette, norm):
        """Determine colors when the hue variable is quantitative."""
        if isinstance(palette, dict):

            # The presence of a norm object overrides a dictionary of hues
            # in specifying a numeric mapping, so we need to process it here.
            levels = list(sorted(palette))
            colors = [palette[k] for k in sorted(palette)]
            cmap = mpl.colors.ListedColormap(colors)
            lookup_table = palette.copy()

        else:

            # The levels are the sorted unique values in the data
            levels = list(np.sort(remove_na(data.unique())))

            # --- Sort out the colormap to use from the palette argument

            # Default numeric palette is our default cubehelix palette
            # TODO do we want to do something complicated to ensure contrast?
            palette = "ch:" if palette is None else palette

            if isinstance(palette, mpl.colors.Colormap):
                cmap = palette
            else:
                cmap = color_palette(palette, as_cmap=True)

            # Now sort out the data normalization
            if norm is None:
                norm = mpl.colors.Normalize()
            elif isinstance(norm, tuple):
                norm = mpl.colors.Normalize(*norm)
            elif not isinstance(norm, mpl.colors.Normalize):
                err = "``hue_norm`` must be None, tuple, or Normalize object."
                raise ValueError(err)

            if not norm.scaled():
                norm(np.asarray(data.dropna()))

            lookup_table = dict(zip(levels, cmap(norm(levels))))

        return levels, lookup_table, norm, cmap


@share_init_params_with_map
class SizeMapping(SemanticMapping):
    """Mapping that sets artist sizes according to data values."""
    # An object that normalizes data values to [0, 1] range
    norm = None

    def __init__(
        self, plotter, sizes=None, order=None, norm=None,
    ):
        """Map the levels of the `size` variable to distinct values.

        Parameters
        ----------
        # TODO add generic parameters

        """
        super().__init__(plotter)

        data = plotter.plot_data.get("size", pd.Series(dtype=float))

        if data.notna().any():

            map_type = self.infer_map_type(
                norm, sizes, plotter.var_types["size"]
            )

            # --- Option 1: numeric mapping

            if map_type == "numeric":

                levels, lookup_table, norm, size_range = self.numeric_mapping(
                    data, sizes, norm,
                )

            # --- Option 2: categorical mapping

            elif map_type == "categorical":

                levels, lookup_table = self.categorical_mapping(
                    data, sizes, order,
                )
                size_range = None

            # --- Option 3: datetime mapping

            # TODO this needs an actual implementation
            else:

                levels, lookup_table = self.categorical_mapping(
                    # Casting data to list to handle differences in the way
                    # pandas and numpy represent datetime64 data
                    list(data), sizes, order,
                )
                size_range = None

            self.map_type = map_type
            self.levels = levels
            self.norm = norm
            self.sizes = sizes
            self.size_range = size_range
            self.lookup_table = lookup_table

    def infer_map_type(self, norm, sizes, var_type):

        if norm is not None:
            map_type = "numeric"
        elif isinstance(sizes, (dict, list)):
            map_type = "categorical"
        else:
            map_type = var_type

        return map_type

    def _lookup_single(self, key):

        try:
            value = self.lookup_table[key]
        except KeyError:
            normed = self.norm(key)
            if np.ma.is_masked(normed):
                normed = np.nan
            value = self.size_range[0] + normed * np.ptp(self.size_range)
        return value

    def categorical_mapping(self, data, sizes, order):

        levels = categorical_order(data, order)

        if isinstance(sizes, dict):

            # Dict inputs map existing data values to the size attribute
            missing = set(levels) - set(sizes)
            if any(missing):
                err = f"Missing sizes for the following levels: {missing}"
                raise ValueError(err)
            lookup_table = sizes.copy()

        elif isinstance(sizes, list):

            # List inputs give size values in the same order as the levels
            if len(sizes) != len(levels):
                err = "The `sizes` list has the wrong number of values."
                raise ValueError(err)

            lookup_table = dict(zip(levels, sizes))

        else:

            if isinstance(sizes, tuple):

                # Tuple input sets the min, max size values
                if len(sizes) != 2:
                    err = "A `sizes` tuple must have only 2 values"
                    raise ValueError(err)

            elif sizes is not None:

                err = f"Value for `sizes` not understood: {sizes}"
                raise ValueError(err)

            else:

                # Otherwise, we need to get the min, max size values from
                # the plotter object we are attached to.

                # TODO this is going to cause us trouble later, because we
                # want to restructure things so that the plotter is generic
                # across the visual representation of the data. But at this
                # point, we don't know the visual representation. Likely we
                # want to change the logic of this Mapping so that it gives
                # points on a normalized range that then gets un-normalized
                # when we know what we're drawing. But given the way the
                # package works now, this way is cleanest.
                sizes = self.plotter._default_size_range

            # For categorical sizes, use regularly-spaced linear steps
            # between the minimum and maximum sizes. Then reverse the
            # ramp so that the largest value is used for the first entry
            # in size_order, etc. This is because "ordered" categories
            # are often though to go in decreasing priority.
            sizes = np.linspace(*sizes, len(levels))[::-1]
            lookup_table = dict(zip(levels, sizes))

        return levels, lookup_table

    def numeric_mapping(self, data, sizes, norm):

        if isinstance(sizes, dict):
            # The presence of a norm object overrides a dictionary of sizes
            # in specifying a numeric mapping, so we need to process it
            # dictionary here
            levels = list(np.sort(list(sizes)))
            size_values = sizes.values()
            size_range = min(size_values), max(size_values)

        else:

            # The levels here will be the unique values in the data
            levels = list(np.sort(remove_na(data.unique())))

            if isinstance(sizes, tuple):

                # For numeric inputs, the size can be parametrized by
                # the minimum and maximum artist values to map to. The
                # norm object that gets set up next specifies how to
                # do the mapping.

                if len(sizes) != 2:
                    err = "A `sizes` tuple must have only 2 values"
                    raise ValueError(err)

                size_range = sizes

            elif sizes is not None:

                err = f"Value for `sizes` not understood: {sizes}"
                raise ValueError(err)

            else:

                # When not provided, we get the size range from the plotter
                # object we are attached to. See the note in the categorical
                # method about how this is suboptimal for future development.
                size_range = self.plotter._default_size_range

        # Now that we know the minimum and maximum sizes that will get drawn,
        # we need to map the data values that we have into that range. We will
        # use a matplotlib Normalize class, which is typically used for numeric
        # color mapping but works fine here too. It takes data values and maps
        # them into a [0, 1] interval, potentially nonlinear-ly.

        if norm is None:
            # Default is a linear function between the min and max data values
            norm = mpl.colors.Normalize()
        elif isinstance(norm, tuple):
            # It is also possible to give different limits in data space
            norm = mpl.colors.Normalize(*norm)
        elif not isinstance(norm, mpl.colors.Normalize):
            err = f"Value for size `norm` parameter not understood: {norm}"
            raise ValueError(err)
        else:
            # If provided with Normalize object, copy it so we can modify
            norm = copy(norm)

        # Set the mapping so all output values are in [0, 1]
        norm.clip = True

        # If the input range is not set, use the full range of the data
        if not norm.scaled():
            norm(levels)

        # Map from data values to [0, 1] range
        sizes_scaled = norm(levels)

        # Now map from the scaled range into the artist units
        if isinstance(sizes, dict):
            lookup_table = sizes
        else:
            lo, hi = size_range
            sizes = lo + sizes_scaled * (hi - lo)
            lookup_table = dict(zip(levels, sizes))

        return levels, lookup_table, norm, size_range


@share_init_params_with_map
class StyleMapping(SemanticMapping):
    """Mapping that sets artist style according to data values."""

    # Style mapping is always treated as categorical
    map_type = "categorical"

    def __init__(
        self, plotter, markers=None, dashes=None, order=None,
    ):
        """Map the levels of the `style` variable to distinct values.

        Parameters
        ----------
        # TODO add generic parameters

        """
        super().__init__(plotter)

        data = plotter.plot_data.get("style", pd.Series(dtype=float))

        if data.notna().any():

            # Cast to list to handle numpy/pandas datetime quirks
            if variable_type(data) == "datetime":
                data = list(data)

            # Find ordered unique values
            levels = categorical_order(data, order)

            markers = self._map_attributes(
                markers, levels, unique_markers(len(levels)), "markers",
            )
            dashes = self._map_attributes(
                dashes, levels, unique_dashes(len(levels)), "dashes",
            )

            # Build the paths matplotlib will use to draw the markers
            paths = {}
            filled_markers = []
            for k, m in markers.items():
                if not isinstance(m, mpl.markers.MarkerStyle):
                    m = mpl.markers.MarkerStyle(m)
                paths[k] = m.get_path().transformed(m.get_transform())
                filled_markers.append(m.is_filled())

            # Mixture of filled and unfilled markers will show line art markers
            # in the edge color, which defaults to white. This can be handled,
            # but there would be additional complexity with specifying the
            # weight of the line art markers without overwhelming the filled
            # ones with the edges. So for now, we will disallow mixtures.
            if any(filled_markers) and not all(filled_markers):
                err = "Filled and line art markers cannot be mixed"
                raise ValueError(err)

            lookup_table = {}
            for key in levels:
                lookup_table[key] = {}
                if markers:
                    lookup_table[key]["marker"] = markers[key]
                    lookup_table[key]["path"] = paths[key]
                if dashes:
                    lookup_table[key]["dashes"] = dashes[key]

            self.levels = levels
            self.lookup_table = lookup_table

    def _lookup_single(self, key, attr=None):
        """Get attribute(s) for a given data point."""
        if attr is None:
            value = self.lookup_table[key]
        else:
            value = self.lookup_table[key][attr]
        return value

    def _map_attributes(self, arg, levels, defaults, attr):
        """Handle the specification for a given style attribute."""
        if arg is True:
            lookup_table = dict(zip(levels, defaults))
        elif isinstance(arg, dict):
            missing = set(levels) - set(arg)
            if missing:
                err = f"These `{attr}` levels are missing values: {missing}"
                raise ValueError(err)
            lookup_table = arg
        elif isinstance(arg, Sequence):
            if len(levels) != len(arg):
                err = f"The `{attr}` argument has the wrong number of values"
                raise ValueError(err)
            lookup_table = dict(zip(levels, arg))
        elif arg:
            err = f"This `{attr}` argument was not understood: {arg}"
            raise ValueError(err)
        else:
            lookup_table = {}

        return lookup_table


# =========================================================================== #


class VectorPlotter:
    """Base class for objects underlying *plot functions."""

    _semantic_mappings = {
        "hue": HueMapping,
        "size": SizeMapping,
        "style": StyleMapping,
    }

    # TODO units is another example of a non-mapping "semantic"
    # we need a general name for this and separate handling
    semantics = "x", "y", "hue", "size", "style", "units"
    wide_structure = {
        "x": "@index", "y": "@values", "hue": "@columns", "style": "@columns",
    }
    flat_structure = {"x": "@index", "y": "@values"}

    _default_size_range = 1, 2  # Unused but needed in tests, ugh

    def __init__(self, data=None, variables={}):

        self._var_levels = {}
        # var_ordered is relevant only for categorical axis variables, and may
        # be better handled by an internal axis information object that tracks
        # such information and is set up by the scale_* methods. The analogous
        # information for numeric axes would be information about log scales.
        self._var_ordered = {"x": False, "y": False}  # alt., used DefaultDict
        self.assign_variables(data, variables)

        for var, cls in self._semantic_mappings.items():

            # Create the mapping function
            map_func = partial(cls.map, plotter=self)
            setattr(self, f"map_{var}", map_func)

            # Call the mapping function to initialize with default values
            getattr(self, f"map_{var}")()

    @classmethod
    def get_semantics(cls, kwargs, semantics=None):
        """Subset a dictionary` arguments with known semantic variables."""
        # TODO this should be get_variables since we have included x and y
        if semantics is None:
            semantics = cls.semantics
        variables = {}
        for key, val in kwargs.items():
            if key in semantics and val is not None:
                variables[key] = val
        return variables

    @property
    def has_xy_data(self):
        """Return True at least one of x or y is defined."""
        return bool({"x", "y"} & set(self.variables))

    @property
    def var_levels(self):
        """Property interface to ordered list of variables levels.

        Each time it's accessed, it updates the var_levels dictionary with the
        list of levels in the current semantic mappers. But it also allows the
        dictionary to persist, so it can be used to set levels by a key. This is
        used to track the list of col/row levels using an attached FacetGrid
        object, but it's kind of messy and ideally fixed by improving the
        faceting logic so it interfaces better with the modern approach to
        tracking plot variables.

        """
        for var in self.variables:
            try:
                map_obj = getattr(self, f"_{var}_map")
                self._var_levels[var] = map_obj.levels
            except AttributeError:
                pass
        return self._var_levels

    def assign_variables(self, data=None, variables={}):
        """Define plot variables, optionally using lookup from `data`."""
        x = variables.get("x", None)
        y = variables.get("y", None)

        if x is None and y is None:
            self.input_format = "wide"
            plot_data, variables = self._assign_variables_wideform(
                data, **variables,
            )
        else:
            self.input_format = "long"
            plot_data, variables = self._assign_variables_longform(
                data, **variables,
            )

        self.plot_data = plot_data
        self.variables = variables
        self.var_types = {
            v: variable_type(
                plot_data[v],
                boolean_type="numeric" if v in "xy" else "categorical"
            )
            for v in variables
        }

        return self

    def _assign_variables_wideform(self, data=None, **kwargs):
        """Define plot variables given wide-form data.

        Parameters
        ----------
        data : flat vector or collection of vectors
            Data can be a vector or mapping that is coerceable to a Series
            or a sequence- or mapping-based collection of such vectors, or a
            rectangular numpy array, or a Pandas DataFrame.
        kwargs : variable -> data mappings
            Behavior with keyword arguments is currently undefined.

        Returns
        -------
        plot_data : :class:`pandas.DataFrame`
            Long-form data object mapping seaborn variables (x, y, hue, ...)
            to data vectors.
        variables : dict
            Keys are defined seaborn variables; values are names inferred from
            the inputs (or None when no name can be determined).

        """
        # Raise if semantic or other variables are assigned in wide-form mode
        assigned = [k for k, v in kwargs.items() if v is not None]
        if any(assigned):
            s = "s" if len(assigned) > 1 else ""
            err = f"The following variable{s} cannot be assigned with wide-form data: "
            err += ", ".join(f"`{v}`" for v in assigned)
            raise ValueError(err)

        # Determine if the data object actually has any data in it
        empty = data is None or not len(data)

        # Then, determine if we have "flat" data (a single vector)
        if isinstance(data, dict):
            values = data.values()
        else:
            values = np.atleast_1d(np.asarray(data, dtype=object))
        flat = not any(
            isinstance(v, Iterable) and not isinstance(v, (str, bytes))
            for v in values
        )

        if empty:

            # Make an object with the structure of plot_data, but empty
            plot_data = pd.DataFrame()
            variables = {}

        elif flat:

            # Handle flat data by converting to pandas Series and using the
            # index and/or values to define x and/or y
            # (Could be accomplished with a more general to_series() interface)
            flat_data = pd.Series(data).copy()
            names = {
                "@values": flat_data.name,
                "@index": flat_data.index.name
            }

            plot_data = {}
            variables = {}

            for var in ["x", "y"]:
                if var in self.flat_structure:
                    attr = self.flat_structure[var]
                    plot_data[var] = getattr(flat_data, attr[1:])
                    variables[var] = names[self.flat_structure[var]]

            plot_data = pd.DataFrame(plot_data)

        else:

            # Otherwise assume we have some collection of vectors.

            # Handle Python sequences such that entries end up in the columns,
            # not in the rows, of the intermediate wide DataFrame.
            # One way to accomplish this is to convert to a dict of Series.
            if isinstance(data, Sequence):
                data_dict = {}
                for i, var in enumerate(data):
                    key = getattr(var, "name", i)
                    # TODO is there a safer/more generic way to ensure Series?
                    # sort of like np.asarray, but for pandas?
                    data_dict[key] = pd.Series(var)

                data = data_dict

            # Pandas requires that dict values either be Series objects
            # or all have the same length, but we want to allow "ragged" inputs
            if isinstance(data, Mapping):
                data = {key: pd.Series(val) for key, val in data.items()}

            # Otherwise, delegate to the pandas DataFrame constructor
            # This is where we'd prefer to use a general interface that says
            # "give me this data as a pandas DataFrame", so we can accept
            # DataFrame objects from other libraries
            wide_data = pd.DataFrame(data, copy=True)

            # At this point we should reduce the dataframe to numeric cols
            numeric_cols = [
                k for k, v in wide_data.items() if variable_type(v) == "numeric"
            ]
            wide_data = wide_data[numeric_cols]

            # Now melt the data to long form
            melt_kws = {"var_name": "@columns", "value_name": "@values"}
            use_index = "@index" in self.wide_structure.values()
            if use_index:
                melt_kws["id_vars"] = "@index"
                try:
                    orig_categories = wide_data.columns.categories
                    orig_ordered = wide_data.columns.ordered
                    wide_data.columns = wide_data.columns.add_categories("@index")
                except AttributeError:
                    category_columns = False
                else:
                    category_columns = True
                wide_data["@index"] = wide_data.index.to_series()

            plot_data = wide_data.melt(**melt_kws)

            if use_index and category_columns:
                plot_data["@columns"] = pd.Categorical(plot_data["@columns"],
                                                       orig_categories,
                                                       orig_ordered)

            # Assign names corresponding to plot semantics
            for var, attr in self.wide_structure.items():
                plot_data[var] = plot_data[attr]

            # Define the variable names
            variables = {}
            for var, attr in self.wide_structure.items():
                obj = getattr(wide_data, attr[1:])
                variables[var] = getattr(obj, "name", None)

            # Remove redundant columns from plot_data
            plot_data = plot_data[list(variables)]

        return plot_data, variables

    def _assign_variables_longform(self, data=None, **kwargs):
        """Define plot variables given long-form data and/or vector inputs.

        Parameters
        ----------
        data : dict-like collection of vectors
            Input data where variable names map to vector values.
        kwargs : variable -> data mappings
            Keys are seaborn variables (x, y, hue, ...) and values are vectors
            in any format that can construct a :class:`pandas.DataFrame` or
            names of columns or index levels in ``data``.

        Returns
        -------
        plot_data : :class:`pandas.DataFrame`
            Long-form data object mapping seaborn variables (x, y, hue, ...)
            to data vectors.
        variables : dict
            Keys are defined seaborn variables; values are names inferred from
            the inputs (or None when no name can be determined).

        Raises
        ------
        ValueError
            When variables are strings that don't appear in ``data``.

        """
        plot_data = {}
        variables = {}

        # Data is optional; all variables can be defined as vectors
        if data is None:
            data = {}

        # TODO should we try a data.to_dict() or similar here to more
        # generally accept objects with that interface?
        # Note that dict(df) also works for pandas, and gives us what we
        # want, whereas DataFrame.to_dict() gives a nested dict instead of
        # a dict of series.

        # Variables can also be extracted from the index attribute
        # TODO is this the most general way to enable it?
        # There is no index.to_dict on multiindex, unfortunately
        try:
            index = data.index.to_frame()
        except AttributeError:
            index = {}

        # The caller will determine the order of variables in plot_data
        for key, val in kwargs.items():

            # First try to treat the argument as a key for the data collection.
            # But be flexible about what can be used as a key.
            # Usually it will be a string, but allow numbers or tuples too when
            # taking from the main data object. Only allow strings to reference
            # fields in the index, because otherwise there is too much ambiguity.
            try:
                val_as_data_key = (
                    val in data
                    or (isinstance(val, (str, bytes)) and val in index)
                )
            except (KeyError, TypeError):
                val_as_data_key = False

            if val_as_data_key:

                # We know that __getitem__ will work

                if val in data:
                    plot_data[key] = data[val]
                elif val in index:
                    plot_data[key] = index[val]
                variables[key] = val

            elif isinstance(val, (str, bytes)):

                # This looks like a column name but we don't know what it means!

                err = f"Could not interpret value `{val}` for parameter `{key}`"
                raise ValueError(err)

            else:

                # Otherwise, assume the value is itself data

                # Raise when data object is present and a vector can't matched
                if isinstance(data, pd.DataFrame) and not isinstance(val, pd.Series):
                    if np.ndim(val) and len(data) != len(val):
                        val_cls = val.__class__.__name__
                        err = (
                            f"Length of {val_cls} vectors must match length of `data`"
                            f" when both are used, but `data` has length {len(data)}"
                            f" and the vector passed to `{key}` has length {len(val)}."
                        )
                        raise ValueError(err)

                plot_data[key] = val

                # Try to infer the name of the variable
                variables[key] = getattr(val, "name", None)

        # Construct a tidy plot DataFrame. This will convert a number of
        # types automatically, aligning on index in case of pandas objects
        plot_data = pd.DataFrame(plot_data)

        # Reduce the variables dictionary to fields with valid data
        variables = {
            var: name
            for var, name in variables.items()
            if plot_data[var].notnull().any()
        }

        return plot_data, variables

    def iter_data(
        self, grouping_vars=None, *,
        reverse=False, from_comp_data=False,
        by_facet=True, allow_empty=False, dropna=True,
    ):
        """Generator for getting subsets of data defined by semantic variables.

        Also injects "col" and "row" into grouping semantics.

        Parameters
        ----------
        grouping_vars : string or list of strings
            Semantic variables that define the subsets of data.
        reverse : bool
            If True, reverse the order of iteration.
        from_comp_data : bool
            If True, use self.comp_data rather than self.plot_data
        by_facet : bool
            If True, add faceting variables to the set of grouping variables.
        allow_empty : bool
            If True, yield an empty dataframe when no observations exist for
            combinations of grouping variables.
        dropna : bool
            If True, remove rows with missing data.

        Yields
        ------
        sub_vars : dict
            Keys are semantic names, values are the level of that semantic.
        sub_data : :class:`pandas.DataFrame`
            Subset of ``plot_data`` for this combination of semantic values.

        """
        # TODO should this default to using all (non x/y?) semantics?
        # or define grouping vars somewhere?
        if grouping_vars is None:
            grouping_vars = []
        elif isinstance(grouping_vars, str):
            grouping_vars = [grouping_vars]
        elif isinstance(grouping_vars, tuple):
            grouping_vars = list(grouping_vars)

        # Always insert faceting variables
        if by_facet:
            facet_vars = {"col", "row"}
            grouping_vars.extend(
                facet_vars & set(self.variables) - set(grouping_vars)
            )

        # Reduce to the semantics used in this plot
        grouping_vars = [
            var for var in grouping_vars if var in self.variables
        ]

        if from_comp_data:
            data = self.comp_data
        else:
            data = self.plot_data

        if dropna:
            data = data.dropna()

        levels = self.var_levels.copy()
        if from_comp_data:
            for axis in {"x", "y"} & set(grouping_vars):
                if self.var_types[axis] == "categorical":
                    if self._var_ordered[axis]:
                        # If the axis is ordered, then the axes in a possible
                        # facet grid are by definition "shared", or there is a
                        # single axis with a unique cat -> idx mapping.
                        # So we can just take the first converter object.
                        converter = self.converters[axis].iloc[0]
                        levels[axis] = converter.convert_units(levels[axis])
                    else:
                        # Otherwise, the mappings may not be unique, but we can
                        # use the unique set of index values in comp_data.
                        levels[axis] = np.sort(data[axis].unique())
                elif self.var_types[axis] == "datetime":
                    levels[axis] = mpl.dates.date2num(levels[axis])
                elif self.var_types[axis] == "numeric" and self._log_scaled(axis):
                    levels[axis] = np.log10(levels[axis])

        if grouping_vars:

            grouped_data = data.groupby(
                grouping_vars, sort=False, as_index=False
            )

            grouping_keys = []
            for var in grouping_vars:
                grouping_keys.append(levels.get(var, []))

            iter_keys = itertools.product(*grouping_keys)
            if reverse:
                iter_keys = reversed(list(iter_keys))

            for key in iter_keys:

                # Pandas fails with singleton tuple inputs
                pd_key = key[0] if len(key) == 1 else key

                try:
                    data_subset = grouped_data.get_group(pd_key)
                except KeyError:
                    # XXX we are adding this to allow backwards compatibility
                    # with the empty artists that old categorical plots would
                    # add (before 0.12), which we may decide to break, in which
                    # case this option could be removed
                    data_subset = data.loc[[]]

                if data_subset.empty and not allow_empty:
                    continue

                sub_vars = dict(zip(grouping_vars, key))

                yield sub_vars, data_subset.copy()

        else:

            yield {}, data.copy()

    @property
    def comp_data(self):
        """Dataframe with numeric x and y, after unit conversion and log scaling."""
        if not hasattr(self, "ax"):
            # Probably a good idea, but will need a bunch of tests updated
            # Most of these tests should just use the external interface
            # Then this can be re-enabled.
            # raise AttributeError("No Axes attached to plotter")
            return self.plot_data

        if not hasattr(self, "_comp_data"):

            comp_data = (
                self.plot_data
                .copy(deep=False)
                .drop(["x", "y"], axis=1, errors="ignore")
            )

            for var in "yx":
                if var not in self.variables:
                    continue

                comp_col = pd.Series(index=self.plot_data.index, dtype=float, name=var)
                grouped = self.plot_data[var].groupby(self.converters[var], sort=False)
                for converter, orig in grouped:
                    with pd.option_context('mode.use_inf_as_null', True):
                        orig = orig.dropna()
                        if var in self.var_levels:
                            # TODO this should happen in some centralized location
                            # it is similar to GH2419, but more complicated because
                            # supporting `order` in categorical plots is tricky
                            orig = orig[orig.isin(self.var_levels[var])]
                    comp = pd.to_numeric(converter.convert_units(orig))
                    if converter.get_scale() == "log":
                        comp = np.log10(comp)
                    comp_col.loc[orig.index] = comp

                comp_data.insert(0, var, comp_col)

            self._comp_data = comp_data

        return self._comp_data

    def _get_axes(self, sub_vars):
        """Return an Axes object based on existence of row/col variables."""
        row = sub_vars.get("row", None)
        col = sub_vars.get("col", None)
        if row is not None and col is not None:
            return self.facets.axes_dict[(row, col)]
        elif row is not None:
            return self.facets.axes_dict[row]
        elif col is not None:
            return self.facets.axes_dict[col]
        elif self.ax is None:
            return self.facets.ax
        else:
            return self.ax

    def _attach(
        self,
        obj,
        allowed_types=None,
        log_scale=None,
    ):
        """Associate the plotter with an Axes manager and initialize its units.

        Parameters
        ----------
        obj : :class:`matplotlib.axes.Axes` or :class:'FacetGrid`
            Structural object that we will eventually plot onto.
        allowed_types : str or list of str
            If provided, raise when either the x or y variable does not have
            one of the declared seaborn types.
        log_scale : bool, number, or pair of bools or numbers
            If not False, set the axes to use log scaling, with the given
            base or defaulting to 10. If a tuple, interpreted as separate
            arguments for the x and y axes.

        """
        from .axisgrid import FacetGrid
        if isinstance(obj, FacetGrid):
            self.ax = None
            self.facets = obj
            ax_list = obj.axes.flatten()
            if obj.col_names is not None:
                self.var_levels["col"] = obj.col_names
            if obj.row_names is not None:
                self.var_levels["row"] = obj.row_names
        else:
            self.ax = obj
            self.facets = None
            ax_list = [obj]

        # Identify which "axis" variables we have defined
        axis_variables = set("xy").intersection(self.variables)

        # -- Verify the types of our x and y variables here.
        # This doesn't really make complete sense being here here, but it's a fine
        # place for it, given  the current system.
        # (Note that for some plots, there might be more complicated restrictions)
        # e.g. the categorical plots have their own check that as specific to the
        # non-categorical axis.
        if allowed_types is None:
            allowed_types = ["numeric", "datetime", "categorical"]
        elif isinstance(allowed_types, str):
            allowed_types = [allowed_types]

        for var in axis_variables:
            var_type = self.var_types[var]
            if var_type not in allowed_types:
                err = (
                    f"The {var} variable is {var_type}, but one of "
                    f"{allowed_types} is required"
                )
                raise TypeError(err)

        # -- Get axis objects for each row in plot_data for type conversions and scaling

        facet_dim = {"x": "col", "y": "row"}

        self.converters = {}
        for var in axis_variables:
            other_var = {"x": "y", "y": "x"}[var]

            converter = pd.Series(index=self.plot_data.index, name=var, dtype=object)
            share_state = getattr(self.facets, f"_share{var}", True)

            # Simplest cases are that we have a single axes, all axes are shared,
            # or sharing is only on the orthogonal facet dimension. In these cases,
            # all datapoints get converted the same way, so use the first axis
            if share_state is True or share_state == facet_dim[other_var]:
                converter.loc[:] = getattr(ax_list[0], f"{var}axis")

            else:

                # Next simplest case is when no axes are shared, and we can
                # use the axis objects within each facet
                if share_state is False:
                    for axes_vars, axes_data in self.iter_data():
                        ax = self._get_axes(axes_vars)
                        converter.loc[axes_data.index] = getattr(ax, f"{var}axis")

                # In the more complicated case, the axes are shared within each
                # "file" of the facetgrid. In that case, we need to subset the data
                # for that file and assign it the first axis in the slice of the grid
                else:

                    names = getattr(self.facets, f"{share_state}_names")
                    for i, level in enumerate(names):
                        idx = (i, 0) if share_state == "row" else (0, i)
                        axis = getattr(self.facets.axes[idx], f"{var}axis")
                        converter.loc[self.plot_data[share_state] == level] = axis

            # Store the converter vector, which we use elsewhere (e.g comp_data)
            self.converters[var] = converter

            # Now actually update the matplotlib objects to do the conversion we want
            grouped = self.plot_data[var].groupby(self.converters[var], sort=False)
            for converter, seed_data in grouped:
                if self.var_types[var] == "categorical":
                    if self._var_ordered[var]:
                        order = self.var_levels[var]
                    else:
                        order = None
                    seed_data = categorical_order(seed_data, order)
                converter.update_units(seed_data)

        # -- Set numerical axis scales

        # First unpack the log_scale argument
        if log_scale is None:
            scalex = scaley = False
        else:
            # Allow single value or x, y tuple
            try:
                scalex, scaley = log_scale
            except TypeError:
                scalex = log_scale if "x" in self.variables else False
                scaley = log_scale if "y" in self.variables else False

        # Now use it
        for axis, scale in zip("xy", (scalex, scaley)):
            if scale:
                for ax in ax_list:
                    set_scale = getattr(ax, f"set_{axis}scale")
                    if scale is True:
                        set_scale("log")
                    else:
                        set_scale("log", base=scale)

        # For categorical y, we want the "first" level to be at the top of the axis
        if self.var_types.get("y", None) == "categorical":
            for ax in ax_list:
                try:
                    ax.yaxis.set_inverted(True)
                except AttributeError:  # mpl < 3.1
                    if not ax.yaxis_inverted():
                        ax.invert_yaxis()

        # TODO -- Add axes labels

    def _log_scaled(self, axis):
        """Return True if specified axis is log scaled on all attached axes."""
        if not hasattr(self, "ax"):
            return False

        if self.ax is None:
            axes_list = self.facets.axes.flatten()
        else:
            axes_list = [self.ax]

        log_scaled = []
        for ax in axes_list:
            data_axis = getattr(ax, f"{axis}axis")
            log_scaled.append(data_axis.get_scale() == "log")

        if any(log_scaled) and not all(log_scaled):
            raise RuntimeError("Axis scaling is not consistent")

        return any(log_scaled)

    def _add_axis_labels(self, ax, default_x="", default_y=""):
        """Add axis labels if not present, set visibility to match ticklabels."""
        # TODO ax could default to None and use attached axes if present
        # but what to do about the case of facets? Currently using FacetGrid's
        # set_axis_labels method, which doesn't add labels to the interior even
        # when the axes are not shared. Maybe that makes sense?
        if not ax.get_xlabel():
            x_visible = any(t.get_visible() for t in ax.get_xticklabels())
            ax.set_xlabel(self.variables.get("x", default_x), visible=x_visible)
        if not ax.get_ylabel():
            y_visible = any(t.get_visible() for t in ax.get_yticklabels())
            ax.set_ylabel(self.variables.get("y", default_y), visible=y_visible)

    # XXX If the scale_* methods are going to modify the plot_data structure, they
    # can't be called twice. That means that if they are called twice, they should
    # raise. Alternatively, we could store an original version of plot_data and each
    # time they are called they operate on the store, not the current state.

    def scale_native(self, axis, *args, **kwargs):

        # Default, defer to matplotlib

        raise NotImplementedError

    def scale_numeric(self, axis, *args, **kwargs):

        # Feels needed to completeness, what should it do?
        # Perhaps handle log scaling? Set the ticker/formatter/limits?

        raise NotImplementedError

    def scale_datetime(self, axis, *args, **kwargs):

        # Use pd.to_datetime to convert strings or numbers to datetime objects
        # Note, use day-resolution for numeric->datetime to match matplotlib

        raise NotImplementedError

    def scale_categorical(self, axis, order=None, formatter=None):
        """
        Enforce categorical (fixed-scale) rules for the data on given axis.

        Parameters
        ----------
        axis : "x" or "y"
            Axis of the plot to operate on.
        order : list
            Order that unique values should appear in.
        formatter : callable
            Function mapping values to a string representation.

        Returns
        -------
        self

        """
        # This method both modifies the internal representation of the data
        # (converting it to string) and sets some attributes on self. It might be
        # a good idea to have a separate object attached to self that contains the
        # information in those attributes (i.e. whether to enforce variable order
        # across facets, the order to use) similar to the SemanticMapping objects
        # we have for semantic variables. That object could also hold the converter
        # objects that get used, if we can decouple those from an existing axis
        # (cf. https://github.com/matplotlib/matplotlib/issues/19229).
        # There are some interactions with faceting information that would need
        # to be thought through, since the converts to use depend on facets.
        # If we go that route, these methods could become "borrowed" methods similar
        # to what happens with the alternate semantic mapper constructors, although
        # that approach is kind of fussy and confusing.

        # TODO this method could also set the grid state? Since we like to have no
        # grid on the categorical axis by default. Again, a case where we'll need to
        # store information until we use it, so best to have a way to collect the
        # attributes that this method sets.

        # TODO if we are going to set visual properties of the axes with these methods,
        # then we could do the steps currently in CategoricalPlotter._adjust_cat_axis

        # TODO another, and distinct idea, is to expose a cut= param here

        _check_argument("axis", ["x", "y"], axis)

        # Categorical plots can be "univariate" in which case they get an anonymous
        # category label on the opposite axis.
        if axis not in self.variables:
            self.variables[axis] = None
            self.var_types[axis] = "categorical"
            self.plot_data[axis] = ""

        # If the "categorical" variable has a numeric type, sort the rows so that
        # the default result from categorical_order has those values sorted after
        # they have been coerced to strings. The reason for this is so that later
        # we can get facet-wise orders that are correct.
        # XXX Should this also sort datetimes?
        # It feels more consistent, but technically will be a default change
        # If so, should also change categorical_order to behave that way
        if self.var_types[axis] == "numeric":
            self.plot_data = self.plot_data.sort_values(axis, kind="mergesort")

        # Now get a reference to the categorical data vector
        cat_data = self.plot_data[axis]

        # Get the initial categorical order, which we do before string
        # conversion to respect the original types of the order list.
        # Track whether the order is given explicitly so that we can know
        # whether or not to use the order constructed here downstream
        self._var_ordered[axis] = order is not None or cat_data.dtype.name == "category"
        order = pd.Index(categorical_order(cat_data, order))

        # Then convert data to strings. This is because in matplotlib,
        # "categorical" data really mean "string" data, so doing this artists
        # will be drawn on the categorical axis with a fixed scale.
        # TODO implement formatter here; check that it returns strings?
        if formatter is not None:
            cat_data = cat_data.map(formatter)
            order = order.map(formatter)
        else:
            cat_data = cat_data.astype(str)
            order = order.astype(str)

        # Update the levels list with the type-converted order variable
        self.var_levels[axis] = order

        # Now ensure that seaborn will use categorical rules internally
        self.var_types[axis] = "categorical"

        # Put the string-typed categorical vector back into the plot_data structure
        self.plot_data[axis] = cat_data

        return self


def unique_dashes(n):
    """Build an arbitrarily long list of unique dash styles for lines.

    Parameters
    ----------
    n : int
        Number of unique dash specs to generate.

    Returns
    -------
    dashes : list of strings or tuples
        Valid arguments for the ``dashes`` parameter on
        :class:`matplotlib.lines.Line2D`. The first spec is a solid
        line (``""``), the remainder are sequences of long and short
        dashes.

    """
    # Start with dash specs that are well distinguishable
    dashes = [
        "",
        (4, 1.5),
        (1, 1),
        (3, 1.25, 1.5, 1.25),
        (5, 1, 1, 1),
    ]

    # Now programmatically build as many as we need
    p = 3
    while len(dashes) < n:

        # Take combinations of long and short dashes
        a = itertools.combinations_with_replacement([3, 1.25], p)
        b = itertools.combinations_with_replacement([4, 1], p)

        # Interleave the combinations, reversing one of the streams
        segment_list = itertools.chain(*zip(
            list(a)[1:-1][::-1],
            list(b)[1:-1]
        ))

        # Now insert the gaps
        for segments in segment_list:
            gap = min(segments)
            spec = tuple(itertools.chain(*((seg, gap) for seg in segments)))
            dashes.append(spec)

        p += 1

    return dashes[:n]


def unique_markers(n):
    """Build an arbitrarily long list of unique marker styles for points.

    Parameters
    ----------
    n : int
        Number of unique marker specs to generate.

    Returns
    -------
    markers : list of string or tuples
        Values for defining :class:`matplotlib.markers.MarkerStyle` objects.
        All markers will be filled.

    """
    # Start with marker specs that are well distinguishable
    markers = [
        "o",
        "X",
        (4, 0, 45),
        "P",
        (4, 0, 0),
        (4, 1, 0),
        "^",
        (4, 1, 45),
        "v",
    ]

    # Now generate more from regular polygons of increasing order
    s = 5
    while len(markers) < n:
        a = 360 / (s + 1) / 2
        markers.extend([
            (s + 1, 1, a),
            (s + 1, 0, a),
            (s, 1, 0),
            (s, 0, 0),
        ])
        s += 1

    # Convert to MarkerStyle object, using only exactly what we need
    # markers = [mpl.markers.MarkerStyle(m) for m in markers[:n]]

    return markers[:n]


def categorical_order(vector, order=None):
    """Return a list of unique data values.

    Determine an ordered list of levels in ``values``.

    Parameters
    ----------
    vector : list, array, Categorical, or Series
        Vector of "categorical" values
    order : list-like, optional
        Desired order of category levels to override the order determined
        from the ``values`` object.

    Returns
    -------
    order : list
        Ordered list of category levels not including null values.

    """
    if order is None:
        if hasattr(vector, "categories"):
            order = vector.categories
        else:
            try:
                order = vector.cat.categories
            except (TypeError, AttributeError):

                try:
                    order = vector.unique()
                except AttributeError:
                    order = pd.unique(vector)

                if variable_type(vector) == "numeric":
                    order = np.sort(order)

        order = filter(pd.notnull, order)
    return list(order)


def infer_orient(x=None, y=None, orient=None, require_numeric=True):
    """Determine how the plot should be oriented based on the data.

    For historical reasons, the convention is to call a plot "horizontally"
    or "vertically" oriented based on the axis representing its dependent
    variable. Practically, this is used when determining the axis for
    numerical aggregation.

    Parameters
    ----------
    x, y : Vector data or None
        Positional data vectors for the plot.
    orient : string or None
        Specified orientation, which must start with "v" or "h" if not None.
    require_numeric : bool
        If set, raise when the implied dependent variable is not numeric.

    Returns
    -------
    orient : "v" or "h"

    Raises
    ------
    ValueError: When `orient` is not None and does not start with "h" or "v"
    TypeError: When dependent variable is not numeric, with `require_numeric`

    """

    x_type = None if x is None else variable_type(x)
    y_type = None if y is None else variable_type(y)

    nonnumeric_dv_error = "{} orientation requires numeric `{}` variable."
    single_var_warning = "{} orientation ignored with only `{}` specified."

    if x is None:
        if str(orient).startswith("h"):
            warnings.warn(single_var_warning.format("Horizontal", "y"))
        if require_numeric and y_type != "numeric":
            raise TypeError(nonnumeric_dv_error.format("Vertical", "y"))
        return "v"

    elif y is None:
        if str(orient).startswith("v"):
            warnings.warn(single_var_warning.format("Vertical", "x"))
        if require_numeric and x_type != "numeric":
            raise TypeError(nonnumeric_dv_error.format("Horizontal", "x"))
        return "h"

    elif str(orient).startswith("v"):
        if require_numeric and y_type != "numeric":
            raise TypeError(nonnumeric_dv_error.format("Vertical", "y"))
        return "v"

    elif str(orient).startswith("h"):
        if require_numeric and x_type != "numeric":
            raise TypeError(nonnumeric_dv_error.format("Horizontal", "x"))
        return "h"

    elif orient is not None:
        err = (
            "`orient` must start with 'v' or 'h' or be None, "
            f"but `{repr(orient)}` was passed."
        )
        raise ValueError(err)

    elif x_type != "categorical" and y_type == "categorical":
        return "h"

    elif x_type != "numeric" and y_type == "numeric":
        return "v"

    elif x_type == "numeric" and y_type != "numeric":
        return "h"

    elif require_numeric and "numeric" not in (x_type, y_type):
        err = "Neither the `x` nor `y` variable appears to be numeric."
        raise TypeError(err)

    else:
        return "v"


class VariableType(UserString):
    """
    Prevent comparisons elsewhere in the library from using the wrong name.

    Errors are simple assertions because users should not be able to trigger
    them. If that changes, they should be more verbose.

    """
    allowed = "numeric", "datetime", "categorical"

    def __init__(self, data):
        assert data in self.allowed, data
        super().__init__(data)

    def __eq__(self, other):
        assert other in self.allowed, other
        return self.data == other


def variable_type(vector, boolean_type="numeric"):
    """
    Determine whether a vector contains numeric, categorical, or datetime data.

    This function differs from the pandas typing API in two ways:

    - Python sequences or object-typed PyData objects are considered numeric if
      all of their entries are numeric.
    - String or mixed-type data are considered categorical even if not
      explicitly represented as a :class:`pandas.api.types.CategoricalDtype`.

    Parameters
    ----------
    vector : :func:`pandas.Series`, :func:`numpy.ndarray`, or Python sequence
        Input data to test.
    boolean_type : 'numeric' or 'categorical'
        Type to use for vectors containing only 0s and 1s (and NAs).

    Returns
    -------
    var_type : 'numeric', 'categorical', or 'datetime'
        Name identifying the type of data in the vector.
    """

    # If a categorical dtype is set, infer categorical
    if pd.api.types.is_categorical_dtype(vector):
        return VariableType("categorical")

    # Special-case all-na data, which is always "numeric"
    if pd.isna(vector).all():
        return VariableType("numeric")

    # Special-case binary/boolean data, allow caller to determine
    # This triggers a numpy warning when vector has strings/objects
    # https://github.com/numpy/numpy/issues/6784
    # Because we reduce with .all(), we are agnostic about whether the
    # comparison returns a scalar or vector, so we will ignore the warning.
    # It triggers a separate DeprecationWarning when the vector has datetimes:
    # https://github.com/numpy/numpy/issues/13548
    # This is considered a bug by numpy and will likely go away.
    with warnings.catch_warnings():
        warnings.simplefilter(
            action='ignore', category=(FutureWarning, DeprecationWarning)
        )
        if np.isin(vector, [0, 1, np.nan]).all():
            return VariableType(boolean_type)

    # Defer to positive pandas tests
    if pd.api.types.is_numeric_dtype(vector):
        return VariableType("numeric")

    if pd.api.types.is_datetime64_dtype(vector):
        return VariableType("datetime")

    # --- If we get to here, we need to check the entries

    # Check for a collection where everything is a number

    def all_numeric(x):
        for x_i in x:
            if not isinstance(x_i, Number):
                return False
        return True

    if all_numeric(vector):
        return VariableType("numeric")

    # Check for a collection where everything is a datetime

    def all_datetime(x):
        for x_i in x:
            if not isinstance(x_i, (datetime, np.datetime64)):
                return False
        return True

    if all_datetime(vector):
        return VariableType("datetime")

    # Otherwise, our final fallback is to consider things categorical

    return VariableType("categorical")


def _default_color(method, hue, color, kws):
    """If needed, get a default color by using the matplotlib property cycle."""
    if hue is not None:
        # This warning is probably user-friendly, but it's currently triggered
        # in a FacetGrid context and I don't want to mess with that logic right now
        #  if color is not None:
        #      msg = "`color` is ignored when `hue` is assigned."
        #      warnings.warn(msg)
        return None

    if color is not None:
        return color

    elif method.__name__ == "plot":

        scout, = method([], [], **kws)
        color = scout.get_color()
        scout.remove()

    elif method.__name__ == "scatter":

        # Matplotlib will raise if the size of x/y don't match s/c,
        # and the latter might be in the kws dict
        scout_size = max(
            np.atleast_1d(kws.get(key, [])).shape[0]
            for key in ["s", "c", "fc", "facecolor", "facecolors"]
        )
        scout_x = scout_y = np.full(scout_size, np.nan)

        scout = method(scout_x, scout_y, **kws)
        facecolors = scout.get_facecolors()

        if not len(facecolors):
            # Handle bug in matplotlib <= 3.2 (I think)
            # This will limit the ability to use non color= kwargs to specify
            # a color in versions of matplotlib with the bug, but trying to
            # work out what the user wanted by re-implementing the broken logic
            # of inspecting the kwargs is probably too brittle.
            single_color = False
        else:
            single_color = np.unique(facecolors, axis=0).shape[0] == 1

        # Allow the user to specify an array of colors through various kwargs
        if "c" not in kws and single_color:
            color = to_rgb(facecolors[0])

        scout.remove()

    elif method.__name__ == "bar":

        # bar() needs masked, not empty data, to generate a patch
        scout, = method([np.nan], [np.nan], **kws)
        color = to_rgb(scout.get_facecolor())
        scout.remove()

    elif method.__name__ == "fill_between":

        # There is a bug on matplotlib < 3.3 where fill_between with
        # datetime units and empty data will set incorrect autoscale limits
        # To workaround it, we'll always return the first color in the cycle.
        # https://github.com/matplotlib/matplotlib/issues/17586

        kws = _normalize_kwargs(kws, mpl.collections.PolyCollection)

        scout = method([], [], **kws)
        facecolor = scout.get_facecolor()
        color = to_rgb(facecolor[0])
        scout.remove()

    return color


def _normalize_kwargs(kws, artist):
    """Wrapper for mpl.cbook.normalize_kwargs that supports <= 3.2.1."""
    _alias_map = {
        'color': ['c'],
        'linewidth': ['lw'],
        'linestyle': ['ls'],
        'facecolor': ['fc'],
        'edgecolor': ['ec'],
        'markerfacecolor': ['mfc'],
        'markeredgecolor': ['mec'],
        'markeredgewidth': ['mew'],
        'markersize': ['ms']
    }
    try:
        kws = normalize_kwargs(kws, artist)
    except AttributeError:
        kws = normalize_kwargs(kws, _alias_map)
    return kws


def _draw_figure(fig):
    """Force draw of a matplotlib figure, accounting for back-compat."""
    # See https://github.com/matplotlib/matplotlib/issues/19197 for context
    fig.canvas.draw()
    if fig.stale:
        try:
            fig.draw(fig.canvas.get_renderer())
        except AttributeError:
            pass


def remove_na(vector):
    """Helper method for removing null values from data vectors.
    Parameters
    ----------
    vector : vector object
        Must implement boolean masking with [] subscript syntax.
    Returns
    -------
    clean_clean : same type as ``vector``
        Vector of data with null values removed. May be a copy or a view.
    """
    return vector[pd.notnull(vector)]


class _CategoricalPlotterNew(VectorPlotter):

    semantics = "x", "y", "hue", "units"

    wide_structure = {"x": "@columns", "y": "@values", "hue": "@columns"}
    flat_structure = {"x": "@index", "y": "@values"}

    def __init__(
        self,
        data=None,
        variables={},
        order=None,
        orient=None,
        require_numeric=False,
    ):

        super().__init__(data=data, variables=variables)

        # This method takes care of some bookkeeping that is necessary because the
        # original categorical plots (prior to the 2021 refactor) had some rules that
        # don't fit exactly into the logic of _core. It may be wise to have a second
        # round of refactoring that moves the logic deeper, but this will keep things
        # relatively sensible for now.

        # The concept of an "orientation" is important to the original categorical
        # plots, but there's no provision for it in _core, so we need to do it here.
        # Note that it could be useful for the other functions in at least two ways
        # (orienting a univariate distribution plot from long-form data and selecting
        # the aggregation axis in lineplot), so we may want to eventually refactor it.
        self.orient = infer_orient(
            x=self.plot_data.get("x", None),
            y=self.plot_data.get("y", None),
            orient=orient,
            require_numeric=require_numeric,
        )

        # Short-circuit in the case of an empty plot
        if not self.has_xy_data:
            return

        # For wide data, orient determines assignment to x/y differently from the
        # wide_structure rules in _core. If we do decide to make orient part of the
        # _core variable assignment, we'll want to figure out how to express that.
        if self.input_format == "wide" and self.orient == "h":
            self.plot_data = self.plot_data.rename(columns={"x": "y", "y": "x"})
            orig_x, orig_y = self.variables["x"], self.variables["y"]
            self.variables.update({"x": orig_y, "y": orig_x})
            orig_x_type, orig_y_type = self.var_types["x"], self.var_types["y"]
            self.var_types.update({"x": orig_y_type, "y": orig_x_type})

        # Categorical plots can be "univariate" in which case they get an anonymous
        # category label on the opposite axis. Note: this duplicates code in the core
        # scale_categorical function. We need to do it here because of the next line.
        if self.cat_axis not in self.variables:
            self.variables[self.cat_axis] = None
            self.var_types[self.cat_axis] = "categorical"
            self.plot_data[self.cat_axis] = ""

        # Categorical variables have discrete levels that we need to track
        cat_levels = categorical_order(self.plot_data[self.cat_axis], order)
        self.var_levels[self.cat_axis] = cat_levels

    def _hue_backcompat(self, color, palette, hue_order, force_hue=False):
        """Implement backwards compatibility for hue parametrization.

        Note: the force_hue parameter is used so that functions can be shown to
        pass existing tests during refactoring and then tested for new behavior.
        It can be removed after completion of the work.

        """
        # The original categorical functions applied a palette to the categorical axis
        # by default. We want to require an explicit hue mapping, to be more consistent
        # with how things work elsewhere now. I don't think there's any good way to
        # do this gently -- because it's triggered by the default value of hue=None,
        # users would always get a warning, unless we introduce some sentinel "default"
        # argument for this change. That's possible, but asking users to set `hue=None`
        # on every call is annoying.
        # We are keeping the logic for implementing the old behavior in with the current
        # system so that (a) we can punt on that decision and (b) we can ensure that
        # refactored code passes old tests.
        default_behavior = color is None or palette is not None
        if force_hue and "hue" not in self.variables and default_behavior:
            self._redundant_hue = True
            self.plot_data["hue"] = self.plot_data[self.cat_axis]
            self.variables["hue"] = self.variables[self.cat_axis]
            self.var_types["hue"] = "categorical"
            hue_order = self.var_levels[self.cat_axis]

            # Because we convert the categorical axis variable to string,
            # we need to update a dictionary palette too
            if isinstance(palette, dict):
                palette = {str(k): v for k, v in palette.items()}

        else:
            self._redundant_hue = False

        # Previously, categorical plots had a trick where color= could seed the palette.
        # Because that's an explicit parameterization, we are going to give it one
        # release cycle with a warning before removing.
        if "hue" in self.variables and palette is None and color is not None:
            if not isinstance(color, str):
                color = mpl.colors.to_hex(color)
            palette = f"dark:{color}"
            msg = (
                "Setting a gradient palette using color= is deprecated and will be "
                f"removed in version 0.13. Set `palette='{palette}'` for same effect."
            )
            warnings.warn(msg, FutureWarning)

        return palette, hue_order

    @property
    def cat_axis(self):
        return {"v": "x", "h": "y"}[self.orient]

    def _get_gray(self, colors):
        """Get a grayscale value that looks good with color."""
        if not len(colors):
            return None
        unique_colors = np.unique(colors, axis=0)
        light_vals = [rgb_to_hls(*rgb[:3])[1] for rgb in unique_colors]
        lum = min(light_vals) * .6
        return (lum, lum, lum)

    def _adjust_cat_axis(self, ax, axis):
        """Set ticks and limits for a categorical variable."""
        # Note: in theory, this could happen in _attach for all categorical axes
        # But two reasons not to do that:
        # - If it happens before plotting, autoscaling messes up the plot limits
        # - It would change existing plots from other seaborn functions
        if self.var_types[axis] != "categorical":
            return

        # We can infer the total number of categories (including those from previous
        # plots that are not part of the plot we are currently making) from the number
        # of ticks, which matplotlib sets up while doing unit conversion. This feels
        # slightly risky, as if we are relying on something that may be a matplotlib
        # implementation detail. But I cannot think of a better way to keep track of
        # the state from previous categorical calls (see GH2516 for context)
        n = len(getattr(ax, f"get_{axis}ticks")())

        if axis == "x":
            ax.xaxis.grid(False)
            ax.set_xlim(-.5, n - .5, auto=None)
        else:
            ax.yaxis.grid(False)
            # Note limits that correspond to previously-inverted y axis
            ax.set_ylim(n - .5, -.5, auto=None)

    @property
    def _native_width(self):
        """Return unit of width separating categories on native numeric scale."""
        unique_values = np.unique(self.comp_data[self.cat_axis])
        if len(unique_values) > 1:
            native_width = np.nanmin(np.diff(unique_values))
        else:
            native_width = 1
        return native_width

    def _nested_offsets(self, width, dodge):
        """Return offsets for each hue level for dodged plots."""
        offsets = None
        if "hue" in self.variables:
            n_levels = len(self._hue_map.levels)
            if dodge:
                each_width = width / n_levels
                offsets = np.linspace(0, width - each_width, n_levels)
                offsets -= offsets.mean()
            else:
                offsets = np.zeros(n_levels)
        return offsets

    # Note that the plotting methods here aim (in most cases) to produce the
    # exact same artists as the original (pre 0.12) version of the code, so
    # there is some weirdness that might not otherwise be clean or make sense in
    # this context, such as adding empty artists for combinations of variables
    # with no observations

    def plot_strips(
        self,
        jitter,
        dodge,
        color,
        edgecolor,
        plot_kws,
    ):

        width = .8 * self._native_width
        offsets = self._nested_offsets(width, dodge)

        if jitter is True:
            jlim = 0.1
        else:
            jlim = float(jitter)
        if "hue" in self.variables and dodge:
            jlim /= len(self._hue_map.levels)
        jlim *= self._native_width
        jitterer = partial(np.random.uniform, low=-jlim, high=+jlim)

        iter_vars = [self.cat_axis]
        if dodge:
            iter_vars.append("hue")

        ax = self.ax
        dodge_move = jitter_move = 0

        for sub_vars, sub_data in self.iter_data(iter_vars,
                                                 from_comp_data=True,
                                                 allow_empty=True):

            if offsets is not None:
                dodge_move = offsets[sub_data["hue"].map(self._hue_map.levels.index)]

            jitter_move = jitterer(size=len(sub_data)) if len(sub_data) > 1 else 0

            adjusted_data = sub_data[self.cat_axis] + dodge_move + jitter_move
            sub_data.loc[:, self.cat_axis] = adjusted_data

            for var in "xy":
                if self._log_scaled(var):
                    sub_data[var] = np.power(10, sub_data[var])

            ax = self._get_axes(sub_vars)
            points = ax.scatter(sub_data["x"], sub_data["y"], color=color, **plot_kws)

            if "hue" in self.variables:
                points.set_facecolors(self._hue_map(sub_data["hue"]))

            if edgecolor == "gray":  # XXX TODO change to "auto"
                points.set_edgecolors(self._get_gray(points.get_facecolors()))
            else:
                points.set_edgecolors(edgecolor)

        # TODO XXX fully implement legend
        show_legend = not self._redundant_hue and self.input_format != "wide"
        if "hue" in self.variables and show_legend:
            for level in self._hue_map.levels:
                color = self._hue_map(level)
                ax.scatter([], [], s=60, color=mpl.colors.rgb2hex(color), label=level)
            ax.legend(loc="best", title=self.variables["hue"])


class _CategoricalPlotter(object):

    width = .8
    default_palette = "light"
    require_numeric = True

    def establish_variables(self, x=None, y=None, hue=None, data=None,
                            orient=None, order=None, hue_order=None,
                            units=None):
        """Convert input specification into a common representation."""
        # Option 1:
        # We are plotting a wide-form dataset
        # -----------------------------------
        if x is None and y is None:

            # Do a sanity check on the inputs
            if hue is not None:
                error = "Cannot use `hue` without `x` and `y`"
                raise ValueError(error)

            # No hue grouping with wide inputs
            plot_hues = None
            hue_title = None
            hue_names = None

            # No statistical units with wide inputs
            plot_units = None

            # We also won't get a axes labels here
            value_label = None
            group_label = None

            # Option 1a:
            # The input data is a Pandas DataFrame
            # ------------------------------------

            if isinstance(data, pd.DataFrame):

                # Order the data correctly
                if order is None:
                    order = []
                    # Reduce to just numeric columns
                    for col in data:
                        if variable_type(data[col]) == "numeric":
                            order.append(col)
                plot_data = data[order]
                group_names = order
                group_label = data.columns.name

                # Convert to a list of arrays, the common representation
                iter_data = plot_data.iteritems()
                plot_data = [np.asarray(s, float) for k, s in iter_data]

            # Option 1b:
            # The input data is an array or list
            # ----------------------------------

            else:

                # We can't reorder the data
                if order is not None:
                    error = "Input data must be a pandas object to reorder"
                    raise ValueError(error)

                # The input data is an array
                if hasattr(data, "shape"):
                    if len(data.shape) == 1:
                        if np.isscalar(data[0]):
                            plot_data = [data]
                        else:
                            plot_data = list(data)
                    elif len(data.shape) == 2:
                        nr, nc = data.shape
                        if nr == 1 or nc == 1:
                            plot_data = [data.ravel()]
                        else:
                            plot_data = [data[:, i] for i in range(nc)]
                    else:
                        error = ("Input `data` can have no "
                                 "more than 2 dimensions")
                        raise ValueError(error)

                # Check if `data` is None to let us bail out here (for testing)
                elif data is None:
                    plot_data = [[]]

                # The input data is a flat list
                elif np.isscalar(data[0]):
                    plot_data = [data]

                # The input data is a nested list
                # This will catch some things that might fail later
                # but exhaustive checks are hard
                else:
                    plot_data = data

                # Convert to a list of arrays, the common representation
                plot_data = [np.asarray(d, float) for d in plot_data]

                # The group names will just be numeric indices
                group_names = list(range((len(plot_data))))

            # Figure out the plotting orientation
            orient = "h" if str(orient).startswith("h") else "v"

        # Option 2:
        # We are plotting a long-form dataset
        # -----------------------------------

        else:

            # See if we need to get variables from `data`
            if data is not None:
                x = data.get(x, x)
                y = data.get(y, y)
                hue = data.get(hue, hue)
                units = data.get(units, units)

            # Validate the inputs
            for var in [x, y, hue, units]:
                if isinstance(var, str):
                    err = "Could not interpret input '{}'".format(var)
                    raise ValueError(err)

            # Figure out the plotting orientation
            orient = infer_orient(
                x, y, orient, require_numeric=self.require_numeric
            )

            # Option 2a:
            # We are plotting a single set of data
            # ------------------------------------
            if x is None or y is None:

                # Determine where the data are
                vals = y if x is None else x

                # Put them into the common representation
                plot_data = [np.asarray(vals)]

                # Get a label for the value axis
                if hasattr(vals, "name"):
                    value_label = vals.name
                else:
                    value_label = None

                # This plot will not have group labels or hue nesting
                groups = None
                group_label = None
                group_names = []
                plot_hues = None
                hue_names = None
                hue_title = None
                plot_units = None

            # Option 2b:
            # We are grouping the data values by another variable
            # ---------------------------------------------------
            else:

                # Determine which role each variable will play
                if orient == "v":
                    vals, groups = y, x
                else:
                    vals, groups = x, y

                # Get the categorical axis label
                group_label = None
                if hasattr(groups, "name"):
                    group_label = groups.name

                # Get the order on the categorical axis
                group_names = categorical_order(groups, order)

                # Group the numeric data
                plot_data, value_label = self._group_longform(vals, groups,
                                                              group_names)

                # Now handle the hue levels for nested ordering
                if hue is None:
                    plot_hues = None
                    hue_title = None
                    hue_names = None
                else:

                    # Get the order of the hue levels
                    hue_names = categorical_order(hue, hue_order)

                    # Group the hue data
                    plot_hues, hue_title = self._group_longform(hue, groups,
                                                                group_names)

                # Now handle the units for nested observations
                if units is None:
                    plot_units = None
                else:
                    plot_units, _ = self._group_longform(units, groups,
                                                         group_names)

        # Assign object attributes
        # ------------------------
        self.orient = orient
        self.plot_data = plot_data
        self.group_label = group_label
        self.value_label = value_label
        self.group_names = group_names
        self.plot_hues = plot_hues
        self.hue_title = hue_title
        self.hue_names = hue_names
        self.plot_units = plot_units

    def _group_longform(self, vals, grouper, order):
        """Group a long-form variable by another with correct order."""
        # Ensure that the groupby will work
        if not isinstance(vals, pd.Series):
            if isinstance(grouper, pd.Series):
                index = grouper.index
            else:
                index = None
            vals = pd.Series(vals, index=index)

        # Group the val data
        grouped_vals = vals.groupby(grouper)
        out_data = []
        for g in order:
            try:
                g_vals = grouped_vals.get_group(g)
            except KeyError:
                g_vals = np.array([])
            out_data.append(g_vals)

        # Get the vals axis label
        label = vals.name

        return out_data, label

    def establish_colors(self, color, palette, saturation):
        """Get a list of colors for the main component of the plots."""
        if self.hue_names is None:
            n_colors = len(self.plot_data)
        else:
            n_colors = len(self.hue_names)

        # Determine the main colors
        if color is None and palette is None:
            # Determine whether the current palette will have enough values
            # If not, we'll default to the husl palette so each is distinct
            current_palette = get_color_cycle()
            if n_colors <= len(current_palette):
                colors = color_palette(n_colors=n_colors)
            else:
                colors = husl_palette(n_colors, l=.7)  # noqa

        elif palette is None:
            # When passing a specific color, the interpretation depends
            # on whether there is a hue variable or not.
            # If so, we will make a blend palette so that the different
            # levels have some amount of variation.
            if self.hue_names is None:
                colors = [color] * n_colors
            else:
                if self.default_palette == "light":
                    colors = light_palette(color, n_colors)
                elif self.default_palette == "dark":
                    colors = dark_palette(color, n_colors)
                else:
                    raise RuntimeError("No default palette specified")
        else:

            # Let `palette` be a dict mapping level to color
            if isinstance(palette, dict):
                if self.hue_names is None:
                    levels = self.group_names
                else:
                    levels = self.hue_names
                palette = [palette[l] for l in levels]

            colors = color_palette(palette, n_colors)

        # Desaturate a bit because these are patches
        if saturation < 1:
            colors = color_palette(colors, desat=saturation)

        # Convert the colors to a common representations
        rgb_colors = color_palette(colors)

        # Determine the gray color to use for the lines framing the plot
        light_vals = [rgb_to_hls(*c)[1] for c in rgb_colors]
        lum = min(light_vals) * .6
        gray = mpl.colors.rgb2hex((lum, lum, lum))

        # Assign object attributes
        self.colors = rgb_colors
        self.gray = gray

    @property
    def hue_offsets(self):
        """A list of center positions for plots when hue nesting is used."""
        n_levels = len(self.hue_names)
        if self.dodge:
            each_width = self.width / n_levels
            offsets = np.linspace(0, self.width - each_width, n_levels)
            offsets -= offsets.mean()
        else:
            offsets = np.zeros(n_levels)

        return offsets

    @property
    def nested_width(self):
        """A float with the width of plot elements when hue nesting is used."""
        if self.dodge:
            width = self.width / len(self.hue_names) * .98
        else:
            width = self.width
        return width

    def annotate_axes(self, ax):
        """Add descriptive labels to an Axes object."""
        if self.orient == "v":
            xlabel, ylabel = self.group_label, self.value_label
        else:
            xlabel, ylabel = self.value_label, self.group_label

        if xlabel is not None:
            ax.set_xlabel(xlabel)
        if ylabel is not None:
            ax.set_ylabel(ylabel)

        group_names = self.group_names
        if not group_names:
            group_names = ["" for _ in range(len(self.plot_data))]

        if self.orient == "v":
            ax.set_xticks(np.arange(len(self.plot_data)))
            ax.set_xticklabels(group_names)
        else:
            ax.set_yticks(np.arange(len(self.plot_data)))
            ax.set_yticklabels(group_names)

        if self.orient == "v":
            ax.xaxis.grid(False)
            ax.set_xlim(-.5, len(self.plot_data) - .5, auto=None)
        else:
            ax.yaxis.grid(False)
            ax.set_ylim(-.5, len(self.plot_data) - .5, auto=None)

        if self.hue_names is not None:
            ax.legend(loc="best", title=self.hue_title)

    def add_legend_data(self, ax, color, label):
        """Add a dummy patch object so we can get legend data."""
        rect = plt.Rectangle([0, 0], 0, 0,
                             linewidth=self.linewidth / 2,
                             edgecolor=self.gray,
                             facecolor=color,
                             label=label)
        ax.add_patch(rect)


class _ViolinPlotter(_CategoricalPlotter):

    def __init__(self, x, y, hue, data, order, hue_order,
                 bw, cut, scale, scale_hue, gridsize,
                 width, inner, split, dodge, orient, linewidth,
                 color, palette, saturation):

        self.establish_variables(x, y, hue, data, orient, order, hue_order)
        self.establish_colors(color, palette, saturation)
        self.estimate_densities(bw, cut, scale, scale_hue, gridsize)

        self.gridsize = gridsize
        self.width = width
        self.dodge = dodge

        if inner is not None:
            if not any([inner.startswith("quart"),
                        inner.startswith("box"),
                        inner.startswith("stick"),
                        inner.startswith("point")]):
                err = "Inner style '{}' not recognized".format(inner)
                raise ValueError(err)
        self.inner = inner

        if split and self.hue_names is not None and len(self.hue_names) != 2:
            msg = "There must be exactly two hue levels to use `split`.'"
            raise ValueError(msg)
        self.split = split

        if linewidth is None:
            linewidth = mpl.rcParams["lines.linewidth"]
        self.linewidth = linewidth

    def estimate_densities(self, bw, cut, scale, scale_hue, gridsize):
        """Find the support and density for all of the data."""
        # Initialize data structures to keep track of plotting data
        if self.hue_names is None:
            support = []
            density = []
            counts = np.zeros(len(self.plot_data))
            max_density = np.zeros(len(self.plot_data))
        else:
            support = [[] for _ in self.plot_data]
            density = [[] for _ in self.plot_data]
            size = len(self.group_names), len(self.hue_names)
            counts = np.zeros(size)
            max_density = np.zeros(size)

        for i, group_data in enumerate(self.plot_data):

            # Option 1: we have a single level of grouping
            # --------------------------------------------

            if self.plot_hues is None:

                # Strip missing datapoints
                kde_data = remove_na(group_data)

                # Handle special case of no data at this level
                if kde_data.size == 0:
                    support.append(np.array([]))
                    density.append(np.array([1.]))
                    counts[i] = 0
                    max_density[i] = 0
                    continue

                # Handle special case of a single unique datapoint
                elif np.unique(kde_data).size == 1:
                    support.append(np.unique(kde_data))
                    density.append(np.array([1.]))
                    counts[i] = 1
                    max_density[i] = 0
                    continue

                # Fit the KDE and get the used bandwidth size
                kde, bw_used = self.fit_kde(kde_data, bw)

                # Determine the support grid and get the density over it
                support_i = self.kde_support(kde_data, bw_used, cut, gridsize)
                density_i = kde.evaluate(support_i)

                # Update the data structures with these results
                support.append(support_i)
                density.append(density_i)
                counts[i] = kde_data.size
                max_density[i] = density_i.max()

            # Option 2: we have nested grouping by a hue variable
            # ---------------------------------------------------

            else:
                for j, hue_level in enumerate(self.hue_names):

                    # Handle special case of no data at this category level
                    if not group_data.size:
                        support[i].append(np.array([]))
                        density[i].append(np.array([1.]))
                        counts[i, j] = 0
                        max_density[i, j] = 0
                        continue

                    # Select out the observations for this hue level
                    hue_mask = self.plot_hues[i] == hue_level

                    # Strip missing datapoints
                    kde_data = remove_na(group_data[hue_mask])

                    # Handle special case of no data at this level
                    if kde_data.size == 0:
                        support[i].append(np.array([]))
                        density[i].append(np.array([1.]))
                        counts[i, j] = 0
                        max_density[i, j] = 0
                        continue

                    # Handle special case of a single unique datapoint
                    elif np.unique(kde_data).size == 1:
                        support[i].append(np.unique(kde_data))
                        density[i].append(np.array([1.]))
                        counts[i, j] = 1
                        max_density[i, j] = 0
                        continue

                    # Fit the KDE and get the used bandwidth size
                    kde, bw_used = self.fit_kde(kde_data, bw)

                    # Determine the support grid and get the density over it
                    support_ij = self.kde_support(kde_data, bw_used,
                                                  cut, gridsize)
                    density_ij = kde.evaluate(support_ij)

                    # Update the data structures with these results
                    support[i].append(support_ij)
                    density[i].append(density_ij)
                    counts[i, j] = kde_data.size
                    max_density[i, j] = density_ij.max()

        # Scale the height of the density curve.
        # For a violinplot the density is non-quantitative.
        # The objective here is to scale the curves relative to 1 so that
        # they can be multiplied by the width parameter during plotting.

        if scale == "area":
            self.scale_area(density, max_density, scale_hue)

        elif scale == "width":
            self.scale_width(density)

        elif scale == "count":
            self.scale_count(density, counts, scale_hue)

        else:
            raise ValueError("scale method '{}' not recognized".format(scale))

        # Set object attributes that will be used while plotting
        self.support = support
        self.density = density

    def fit_kde(self, x, bw):
        """Estimate a KDE for a vector of data with flexible bandwidth."""
        kde = gaussian_kde(x, bw)

        # Extract the numeric bandwidth from the KDE object
        bw_used = kde.factor

        # At this point, bw will be a numeric scale factor.
        # To get the actual bandwidth of the kernel, we multiple by the
        # unbiased standard deviation of the data, which we will use
        # elsewhere to compute the range of the support.
        bw_used = bw_used * x.std(ddof=1)

        return kde, bw_used

    def kde_support(self, x, bw, cut, gridsize):
        """Define a grid of support for the violin."""
        support_min = x.min() - bw * cut
        support_max = x.max() + bw * cut
        return np.linspace(support_min, support_max, gridsize)

    def scale_area(self, density, max_density, scale_hue):
        """Scale the relative area under the KDE curve.

        This essentially preserves the "standard" KDE scaling, but the
        resulting maximum density will be 1 so that the curve can be
        properly multiplied by the violin width.

        """
        if self.hue_names is None:
            for d in density:
                if d.size > 1:
                    d /= max_density.max()
        else:
            for i, group in enumerate(density):
                for d in group:
                    if scale_hue:
                        max = max_density[i].max()
                    else:
                        max = max_density.max()
                    if d.size > 1:
                        d /= max

    def scale_width(self, density):
        """Scale each density curve to the same height."""
        if self.hue_names is None:
            for d in density:
                d /= d.max()
        else:
            for group in density:
                for d in group:
                    d /= d.max()

    def scale_count(self, density, counts, scale_hue):
        """Scale each density curve by the number of observations."""
        if self.hue_names is None:
            if counts.max() == 0:
                d = 0
            else:
                for count, d in zip(counts, density):
                    d /= d.max()
                    d *= count / counts.max()
        else:
            for i, group in enumerate(density):
                for j, d in enumerate(group):
                    if counts[i].max() == 0:
                        d = 0
                    else:
                        count = counts[i, j]
                        if scale_hue:
                            scaler = count / counts[i].max()
                        else:
                            scaler = count / counts.max()
                        d /= d.max()
                        d *= scaler

    @property
    def dwidth(self):

        if self.hue_names is None or not self.dodge:
            return self.width / 2
        elif self.split:
            return self.width / 2
        else:
            return self.width / (2 * len(self.hue_names))

    def draw_violins(self, ax):
        """Draw the violins onto `ax`."""
        fill_func = ax.fill_betweenx if self.orient == "v" else ax.fill_between
        for i, group_data in enumerate(self.plot_data):

            kws = dict(edgecolor=self.gray, linewidth=self.linewidth)

            # Option 1: we have a single level of grouping
            # --------------------------------------------

            if self.plot_hues is None:

                support, density = self.support[i], self.density[i]

                # Handle special case of no observations in this bin
                if support.size == 0:
                    continue

                # Handle special case of a single observation
                elif support.size == 1:
                    val = support.item()
                    d = density.item()
                    self.draw_single_observation(ax, i, val, d)
                    continue

                # Draw the violin for this group
                grid = np.ones(self.gridsize) * i
                fill_func(support,
                          grid - density * self.dwidth,
                          grid + density * self.dwidth,
                          facecolor=self.colors[i],
                          **kws)

                # Draw the interior representation of the data
                if self.inner is None:
                    continue

                # Get a nan-free vector of datapoints
                violin_data = remove_na(group_data)

                # Draw box and whisker information
                if self.inner.startswith("box"):
                    self.draw_box_lines(ax, violin_data, support, density, i)

                # Draw quartile lines
                elif self.inner.startswith("quart"):
                    self.draw_quartiles(ax, violin_data, support, density, i)

                # Draw stick observations
                elif self.inner.startswith("stick"):
                    self.draw_stick_lines(ax, violin_data, support, density, i)

                # Draw point observations
                elif self.inner.startswith("point"):
                    self.draw_points(ax, violin_data, i)

            # Option 2: we have nested grouping by a hue variable
            # ---------------------------------------------------

            else:
                offsets = self.hue_offsets
                for j, hue_level in enumerate(self.hue_names):

                    support, density = self.support[i][j], self.density[i][j]
                    kws["facecolor"] = self.colors[j]

                    # Add legend data, but just for one set of violins
                    if not i:
                        self.add_legend_data(ax, self.colors[j], hue_level)

                    # Handle the special case where we have no observations
                    if support.size == 0:
                        continue

                    # Handle the special case where we have one observation
                    elif support.size == 1:
                        val = support.item()
                        d = density.item()
                        if self.split:
                            d = d / 2
                        at_group = i + offsets[j]
                        self.draw_single_observation(ax, at_group, val, d)
                        continue

                    # Option 2a: we are drawing a single split violin
                    # -----------------------------------------------

                    if self.split:

                        grid = np.ones(self.gridsize) * i
                        if j:
                            fill_func(support,
                                      grid,
                                      grid + density * self.dwidth,
                                      **kws)
                        else:
                            fill_func(support,
                                      grid - density * self.dwidth,
                                      grid,
                                      **kws)

                        # Draw the interior representation of the data
                        if self.inner is None:
                            continue

                        # Get a nan-free vector of datapoints
                        hue_mask = self.plot_hues[i] == hue_level
                        violin_data = remove_na(group_data[hue_mask])

                        # Draw quartile lines
                        if self.inner.startswith("quart"):
                            self.draw_quartiles(ax, violin_data,
                                                support, density, i,
                                                ["left", "right"][j])

                        # Draw stick observations
                        elif self.inner.startswith("stick"):
                            self.draw_stick_lines(ax, violin_data,
                                                  support, density, i,
                                                  ["left", "right"][j])

                        # The box and point interior plots are drawn for
                        # all data at the group level, so we just do that once
                        if not j:
                            continue

                        # Get the whole vector for this group level
                        violin_data = remove_na(group_data)

                        # Draw box and whisker information
                        if self.inner.startswith("box"):
                            self.draw_box_lines(ax, violin_data,
                                                support, density, i)

                        # Draw point observations
                        elif self.inner.startswith("point"):
                            self.draw_points(ax, violin_data, i)

                    # Option 2b: we are drawing full nested violins
                    # -----------------------------------------------

                    else:
                        grid = np.ones(self.gridsize) * (i + offsets[j])
                        fill_func(support,
                                  grid - density * self.dwidth,
                                  grid + density * self.dwidth,
                                  **kws)

                        # Draw the interior representation
                        if self.inner is None:
                            continue

                        # Get a nan-free vector of datapoints
                        hue_mask = self.plot_hues[i] == hue_level
                        violin_data = remove_na(group_data[hue_mask])

                        # Draw box and whisker information
                        if self.inner.startswith("box"):
                            self.draw_box_lines(ax, violin_data,
                                                support, density,
                                                i + offsets[j])

                        # Draw quartile lines
                        elif self.inner.startswith("quart"):
                            self.draw_quartiles(ax, violin_data,
                                                support, density,
                                                i + offsets[j])

                        # Draw stick observations
                        elif self.inner.startswith("stick"):
                            self.draw_stick_lines(ax, violin_data,
                                                  support, density,
                                                  i + offsets[j])

                        # Draw point observations
                        elif self.inner.startswith("point"):
                            self.draw_points(ax, violin_data, i + offsets[j])

    def draw_single_observation(self, ax, at_group, at_quant, density):
        """Draw a line to mark a single observation."""
        d_width = density * self.dwidth
        if self.orient == "v":
            ax.plot([at_group - d_width, at_group + d_width],
                    [at_quant, at_quant],
                    color=self.gray,
                    linewidth=self.linewidth)
        else:
            ax.plot([at_quant, at_quant],
                    [at_group - d_width, at_group + d_width],
                    color=self.gray,
                    linewidth=self.linewidth)

    def draw_box_lines(self, ax, data, support, density, center):
        """Draw boxplot information at center of the density."""
        # Compute the boxplot statistics
        q25, q50, q75 = np.percentile(data, [25, 50, 75])
        whisker_lim = 1.5 * (q75 - q25)
        h1 = np.min(data[data >= (q25 - whisker_lim)])
        h2 = np.max(data[data <= (q75 + whisker_lim)])

        # Draw a boxplot using lines and a point
        if self.orient == "v":
            ax.plot([center, center], [h1, h2],
                    linewidth=self.linewidth,
                    color=self.gray)
            ax.plot([center, center], [q25, q75],
                    linewidth=self.linewidth * 3,
                    color=self.gray)
            ax.scatter(center, q50,
                       zorder=3,
                       color="white",
                       edgecolor=self.gray,
                       s=np.square(self.linewidth * 2))
        else:
            ax.plot([h1, h2], [center, center],
                    linewidth=self.linewidth,
                    color=self.gray)
            ax.plot([q25, q75], [center, center],
                    linewidth=self.linewidth * 3,
                    color=self.gray)
            ax.scatter(q50, center,
                       zorder=3,
                       color="white",
                       edgecolor=self.gray,
                       s=np.square(self.linewidth * 2))

    def draw_quartiles(self, ax, data, support, density, center, split=False):
        """Draw the quartiles as lines at width of density."""
        q25, q50, q75 = np.percentile(data, [25, 50, 75])

        self.draw_to_density(ax, center, q25, support, density, split,
                             linewidth=self.linewidth,
                             dashes=[self.linewidth * 1.5] * 2)
        self.draw_to_density(ax, center, q50, support, density, split,
                             linewidth=self.linewidth,
                             dashes=[self.linewidth * 3] * 2)
        self.draw_to_density(ax, center, q75, support, density, split,
                             linewidth=self.linewidth,
                             dashes=[self.linewidth * 1.5] * 2)

    def draw_points(self, ax, data, center):
        """Draw individual observations as points at middle of the violin."""
        kws = dict(s=np.square(self.linewidth * 2),
                   color=self.gray,
                   edgecolor=self.gray)

        grid = np.ones(len(data)) * center

        if self.orient == "v":
            ax.scatter(grid, data, **kws)
        else:
            ax.scatter(data, grid, **kws)

    def draw_stick_lines(self, ax, data, support, density,
                         center, split=False):
        """Draw individual observations as sticks at width of density."""
        for val in data:
            self.draw_to_density(ax, center, val, support, density, split,
                                 linewidth=self.linewidth * .5)

    def draw_to_density(self, ax, center, val, support, density, split, **kws):
        """Draw a line orthogonal to the value axis at width of density."""
        idx = np.argmin(np.abs(support - val))
        width = self.dwidth * density[idx] * .99

        kws["color"] = self.gray

        if self.orient == "v":
            if split == "left":
                ax.plot([center - width, center], [val, val], **kws)
            elif split == "right":
                ax.plot([center, center + width], [val, val], **kws)
            else:
                ax.plot([center - width, center + width], [val, val], **kws)
        else:
            if split == "left":
                ax.plot([val, val], [center - width, center], **kws)
            elif split == "right":
                ax.plot([val, val], [center, center + width], **kws)
            else:
                ax.plot([val, val], [center - width, center + width], **kws)

    def plot(self, ax):
        """Make the violin plot."""
        self.draw_violins(ax)
        self.annotate_axes(ax)
        if self.orient == "h":
            ax.invert_yaxis()


def violinplot(
    *,
    x=None, y=None,
    hue=None, data=None,
    order=None, hue_order=None,
    bw="scott", cut=2, scale="area", scale_hue=True, gridsize=100,
    width=.8, inner="box", split=False, dodge=True, orient=None,
    linewidth=None, color=None, palette=None, saturation=.75,
    ax=None, **kwargs,
):

    plotter = _ViolinPlotter(x, y, hue, data, order, hue_order,
                             bw, cut, scale, scale_hue, gridsize,
                             width, inner, split, dodge, orient, linewidth,
                             color, palette, saturation)

    if ax is None:
        ax = plt.gca()

    plotter.plot(ax)
    return ax


def stripplot(
    *,
    x=None, y=None,
    hue=None, data=None,
    order=None, hue_order=None,
    jitter=True, dodge=False, orient=None, color=None, palette=None,
    size=5, edgecolor="gray", linewidth=0, ax=None,
    hue_norm=None, fixed_scale=True, formatter=None,
    **kwargs
):

    # XXX we need to add a legend= param!!!

    p = _CategoricalPlotterNew(
        data=data,
        variables=_CategoricalPlotterNew.get_semantics(locals()),
        order=order,
        orient=orient,
        require_numeric=False,
    )

    if ax is None:
        ax = plt.gca()

    if fixed_scale or p.var_types[p.cat_axis] == "categorical":
        p.scale_categorical(p.cat_axis, order=order, formatter=formatter)

    p._attach(ax)

    palette, hue_order = p._hue_backcompat(color, palette, hue_order)

    color = _default_color(ax.scatter, hue, color, kwargs)

    p.map_hue(palette=palette, order=hue_order, norm=hue_norm)

    # XXX Copying possibly bad default decisions from original code for now
    kwargs.setdefault("zorder", 3)
    size = kwargs.get("s", size)

    kwargs.update(dict(
        s=size ** 2,
        edgecolor=edgecolor,
        linewidth=linewidth)
    )

    p.plot_strips(
        jitter=jitter,
        dodge=dodge,
        color=color,
        edgecolor=edgecolor,
        plot_kws=kwargs,
    )

    # XXX this happens inside a plotting method in the distribution plots
    # but maybe it's better out here? Alternatively, we have an open issue
    # suggesting that _attach could add default axes labels, which seems smart.
    p._add_axis_labels(ax)
    p._adjust_cat_axis(ax, axis=p.cat_axis)

    return ax
