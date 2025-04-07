# fedcal _cls_utils.py
#
# Copyright (c) 2023-2024 Adam Poulemanos. All rights reserved.
#
# fedcal is open source software subject to the terms of the
# MIT license, found in the
# [GitHub source directory](https://github.com/psuedomagi/fedcal)
# in the LICENSE.md file.
#
# It may be freely distributed, reused, modified, and distributed under the
# terms of that license, but must be accompanied by the license and the
# accompanying copyright notice.

"""
The private _cls_utils module provides supporting utilities to add
functionality for fedcal classes and API experience. Not yet implemented;
includes SeriesExporter and to_series, a class and decorator for
converting numpy arrays and pandas indexes to pandas Series with the
datetimeindex of the function/class as its index.

Where we planned to use this, the output is currently in property methods
(i.e. FedIndex); which interferes with the wrapper and we probably need to
rethink the approach.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from attr import define, field
from funcy import decorator
from numpy.typing import NDArray
from pandas import DatetimeIndex, Series

from fedcal._base import MagicDelegator


class NPArrayImposter(
    metaclass=MagicDelegator, delegate_to="array", delegate_class=np.ndarray
):
    def __init__(
        self,
        array: NDArray | None = None,
        datetimeindex: DatetimeIndex | None = None,
    ) -> None:
        self.array: NDArray = array or np.array(object=[])
        self.datetimeindex: DatetimeIndex | None = datetimeindex or None

    def __getattr__(self, name: str) -> Any:
        """
        Delegates attribute access to the ts attribute. This lets
        FedStamp objects use any methods/attributes of Timestamp.

        Parameters
        ----------
        name : The name of the attribute to retrieve.

        Returns
        -------
        The value of the attribute.
        """

        # this shouldn't be necessary, but... seems to be until I can debug
        if name in self.__class__.__dict__:
            return self.__class__.__dict__[name].__get__(self, self.__class__)

        if hasattr(self.array, name):
            return getattr(self.array, name)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getattribute__(self, name: str) -> Any:
        """
        We set __getattribute__ manually to ensure it overrides
        any delegation to pd.Timestamp from our metaclass.
        (It shouldn't, I know, but I swear it was. Requires further
        investigation.)

        Parameters
        ----------
        name
            name of attribute

        Returns
        -------
            attribute if found.
        """
        return object.__getattribute__(self, name)

    def to_series(self, name: str = None, dtype: Any = None) -> Series:
        if not hasattr(self.array, "__iter__"):
            self.array = [self.array]
        return pd.Series(
            data=self.array, index=self.datetimeindex, name=name, dtype=dtype
        )


@define()
class SeriesExporter:
    array: NDArray | pd.Index | pd.PeriodIndex | pd.Series | None = field()
    datetimeindex: DatetimeIndex | None = field(default=None)

    def array_to_series(self, name: str = None, dtype: Any = None) -> Series:
        if not hasattr(self.array, "__iter__"):
            self.array = [self.array]
        return pd.Series(
            data=self.array, index=self.datetimeindex, name=name, dtype=dtype
        )


@decorator
def to_series(
    call, to_series: bool = False, name: str = None, dtype: Any = None
) -> Series | np.ndarray | pd.Index | pd.PeriodIndex:
    result: "np.ndarray" = call()

    def fetch_datetimeindex() -> DatetimeIndex | None:
        for source in [call._kwargs, call._locals, getattr(call._func, "self", None)]:
            datetimeindex: DatetimeIndex = source.get("datetimeindex") or source.get(
                "dates"
            )
            if isinstance(datetimeindex, pd.DatetimeIndex):
                return datetimeindex
            if isinstance(source, dict):
                for vals in source.values():
                    if isinstance(vals, pd.DatetimeIndex):
                        return vals
            else:
                for attr in vars(source).values():
                    if isinstance(attr, pd.DatetimeIndex):
                        return attr

    if to_series:
        datetimeindex: DatetimeIndex | None = fetch_datetimeindex()
        exporter = SeriesExporter(array=result, datetimeindex=datetimeindex)
        return exporter.array_to_series(name=name, dtype=dtype)
    return result
