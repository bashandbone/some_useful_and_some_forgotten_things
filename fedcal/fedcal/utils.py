# fedcal utils.py
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
utils.py provides a number of helper converter functions for handling
time conversions in fedcal. We expose it publicly because they're probably
generally useful for other things.

It includes:
- `iso_to_ts` streamlines conversion of ISO8601 formatted strings to pandas
Timestamp, primarily for loading json status input in _status_factory.py

- `get_today` and `ts_to_posix_day` for
handling POSIX-day integer second retrieval for today and from pandas
Timestamp objects respectively.

- `ensure_datetimeindex` a converter that normalizes a variety of input to
DatetimeIndex for consistent handling

- `to_dt64` a converter that normalizes a variety of input to numpy.datetime64
for consistent handling. Primarily used for back-end custom DateOffset object
calculations.

- `dt64_to_date` converts an array (or scalar) of numpy.datetime64 to integer
y, m, d using numpy vectorized operations. Primarily used for custom
DateOffset object calculations.

- `dt64_to_dow` converts an array (or scalar) of numpy.datetime64 to integer
dow using numpy vectorized operations. Primarily used for custom DateOffset
object calculations.

- `to_timestamp` and `to_datetimeindex` are singledispatch converter functions
for converting a wide range of possible time inputs to `pd.Timestamp` and
`pd.DatetimeIndex` respectively. As they can look complex for the uninitiated
let's dive in deeper:

- `to_timestamp` routes input based on type (that's what a singledispatch is)
to helper converters, most of which prep input for conversion to `pd.
Timestamp`. Those converters then route output through a wrapper,
`check_timestamp`, which centralizes conversions to `pd.Timestamp` so
we're not repeating ourselves in each of the converters. `check_timestamp`
wraps `_normalize_timestamp`, which normalizes timezone-aware `pd.Timestamps`
to U.S. Eastern (because Washington D.C.).

- `to_datetimeindex` is similar to `to_timestamp`, but is itself wrapped
by `wrap_tuple`, which intercepts two argument formatted input (i.e.
start-date, end_date) and outputs it as a single argument tuple (i.e.
(start_date, end_date)). Most input is then processed through `to_timestamp`
with the tuple's two dates routed separately. That keeps us from repeating
ourselves. `to_datetimeindex` does add functionality for conversions from
array-like objects (i.e. numpy arrays) to `pd.DatetimeIndex` objects.
After conversion, tupled start/end dates are passed through
`_get_datetimeindex_for_range` and all input is finally passed
through `_normalize_datetimeindex` to normalize timezone aware
input to U.S. Eastern, as with `to_timestamp`.
"""
from __future__ import annotations

import datetime
from array import ArrayType
from dataclasses import dataclass, field
from functools import singledispatch
from typing import Any, Self

import numpy as np
import pandas as pd
from funcy import decorator
from numpy import ScalarType, datetime64, int32, int64, uint8
from numpy.typing import NDArray
from pandas import DatetimeIndex, Index, PeriodIndex, Series, Timestamp
from pandas.tseries.frequencies import to_offset

from fedcal._typing import (
    DatetimeScalarOrArray,
    FedIndexConvertibleTypes,
    FedStampConvertibleTypes,
)

datetime_types = (
    datetime.datetime,
    datetime.date,
    pd.Timestamp,
    np.datetime64,
    np.int64,
)
array_types = (np.ndarray, pd.DatetimeIndex, pd.Series)

datetime_keys: list[str] = [
    "arr",
    "array",
    "date",
    "dates",
    "datetime",
    "datetimeindex",
    "dt",
    "dtarr",
    "time",
    "timestamp",
]


def find_nearest(
    items: ArrayType | ScalarType, pivot: ScalarType
) -> ArrayType | ScalarType:
    """
    Implementation of Tamas Hegedus' solution on StackOverflow:
    https://stackoverflow.com/questions/32237862/find-the-closest-date-to-a-given-date

    Can find nearest value in items to pivot for any two arguments
    that support comparison, subtraction and abs, including datetime-like
    objects.

    Parameters
    ----------
    items : values to compare with pivot
    pivot : value to find the closest item to

    Returns
    -------
    nearest item(s) in items to pivot

    """
    return min(items, key=lambda x: abs(x - pivot))


def iso_to_ts(t: str, fmt: str | None = None) -> Timestamp:
    """
    Short and quick string to datetime conversion specifically for
    loading intervals.

    Parameters
    ----------
    t : str
        The string to convert.
    fmt : str, optional, defaults to ISO08601
    Returns
    -------
    Timestamp
    """
    t_fmt: str = fmt or "ISO8601"
    return pd.to_datetime(arg=t, format=t_fmt)


def get_today() -> Timestamp:
    """
    Returns the current date as a Timestamp.

    Returns
    -------
    Current date as a normalized Timestamp.

    """
    return pd.Timestamp.utcnow().normalize()


def ts_to_posix_day(timestamp: Timestamp) -> int:
    """
    Converts a pandas Timestamp object to a POSIX-day integer timestamp.

    Parameters
    ----------
    timestamp : pandas Timestamp object

    Returns
    -------
    int
        POSIX-day timestamp in days.

    """
    return int(timestamp.normalize().timestamp() // 86400)


def check_dt_in_array(arr: NDArray | DatetimeIndex | Series) -> bool:
    """
    Checks an array for datetime-like objects

    Parameters
    ----------
    arr : array-like object to check

    Returns
    -------
    bool
        True if datetime-like objects are found in the array, False otherwise.
    """
    if isinstance(arr, pd.DatetimeIndex):
        return True
    type_check = str(arr.dtype)
    return bool(
        type_check.startswith(("datetime", "<M8", "int")) or type_check == "Timestamp"
    )


def is_datetime_like(val=None) -> bool:
    """
    Checks if a value is datetime-like or an array that contains datetimes.

    Parameters
    ----------
    val, optional : value to check, by default None

    Returns
    -------
        True if object is datetime-like, False otherwise.
    """
    if isinstance(val, (tuple, list, dict)):
        return any(is_datetime_like(val=v) for v in val)
    return isinstance(val, datetime_types) or (
        isinstance(val, array_types) and check_dt_in_array(arr=val)
    )


def find_datetime(
    *args, **kwargs
) -> tuple[DatetimeScalarOrArray, str] | DatetimeScalarOrArray | None:
    """
    Finds the first argument that is a datetime object.

    Parameters
    ----------
    args : list of arguments
    kwargs : dict of keyword arguments

    Returns
    -------
    Datetime object or None
    """
    for key, value in kwargs.items():
        if is_datetime_like(val=value):
            return value, key
        if key in datetime_keys and value:
            value = value[0] if isinstance(value, (tuple, list)) else value
            return (value, key)
    for arg in args:
        if isinstance(arg, tuple):
            for elem in arg:
                if is_datetime_like(val=elem):
                    return elem
        elif is_datetime_like(val=arg):
            return arg
    return None


def ensure_datetimeindex(dt: DatetimeScalarOrArray | None = None) -> Any:
    """
    Ensures that the argument is a DatetimeIndex.

    Parameters
    ----------
    dt : datetime-like object to convert to DatetimeIndex

    Returns
    -------
    pd.DatetimeIndex object of the input datetime-like object
    """

    return pd.DatetimeIndex(
        data=[dt] if isinstance(dt, (pd.Timestamp, np.datetime64)) else dt
    )


def to_dt64(
    dt: DatetimeScalarOrArray | None = None, freq: str = "D", to_int64: bool = False
) -> NDArray[datetime64 | int64] | datetime64 | int64:
    """
    Converts date input to numpy datetime64 array or scalar or optionally
    int64 timestamp.

    Arguments
    ---------
    dt : datetime-like object to convert

    freq : optional string frequency for datetime64 conversion, defaults to
        'D'. Must be a valid frequency (e.g. 'D', 's', 'us', 'ns')

    to_int64: boolean flag to instead convert output to int64 nanoseconds
        since the epoch.

    Returns
    -------
    Converted array or scalar
    """
    dt_type = "int64" if to_int64 else f"datetime64[{freq}]"
    return (
        dt.astype(dt_type)
        if isinstance(dt, (np.ndarray, datetime64))
        else pd.to_datetime(dt).normalize().to_numpy().astype(dtype=dt_type)
    )


def dt64_to_date(dtarr: NDArray[datetime64]) -> NDArray[int32]:
    """
    Adapted from RBF06:
    https://stackoverflow.com/questions/13648774/get-year-month-or-day-from-numpy-datetime64#26895491

    Convert array of datetime64 to a calendar array of year, month, day with
    these quantities indexed on the last axis.

    Parameters
    ----------
    dt : datetime64 array (...)
        numpy.ndarray of datetimes of arbitrary shape

    Returns
    -------
    uint32 array (..., 4)
        calendar array with last axis representing year, month, day
    """
    dtarr = to_dt64(dt=dtarr, freq="ns")
    out: NDArray[Any] = np.empty(shape=dtarr.shape + (4,), dtype="u4")
    Y, M, D = [dtarr.astype(dtype=f"M8[{x}]") for x in "YMD"]
    out[..., 0] = dtarr.astype(dtype="datetime64[D]")
    out[..., 1] = Y + 1970
    out[..., 2] = (M - Y) + 1
    out[..., 3] = (D - M) + 1

    return out


def dt64_to_dow(dtarr: NDArray[datetime64]) -> NDArray[datetime64 | int64]:
    """
    Adapted from jwdink on stackoverflow:
    https://stackoverflow.com/questions/52398383/finding-day-of-the-week-for-a-datetime64

    Convert array of datetime64 to an array of days of the week.

    Parameters
    ----------
    dtarr : datetime64 array (...)
        numpy.ndarray of datetimes of arbitrary shape

    Returns
    -------
    int64 array
        array with axis representing day of week
    """
    dtarr = to_dt64(dt=dtarr, freq="ns")
    out: NDArray[uint8] = np.empty(shape=dtarr.shape + (2,), dtype=uint8)
    out[..., 0] = dtarr
    out[..., 1] = (dtarr.view(dtype="int64") - 4) % 7
    return out


@singledispatch
def to_timestamp(date_input: FedStampConvertibleTypes) -> Timestamp | None:
    """
    We want to handle diverse date inputs without tripping, because one
    goal of our library is to provide a feature-rich addition that
    seamlessly behaves like and integrates into pandas. This
    singledispatch function allows us to funnel diverse inputs for conversion
    based on type without repeating ourselves.

    We roll our own here because pd.to_datetime has multiple outputs depending
    on input type, and we want to consistently get Timestamps and normalize
    them. This also allows us to add some flexibility to how to_datetime
    handles input.

    Parameters
    ----------
    date_input : Any FedStampConvertibleTypes for conversion to a time zone
    normalized Timestamp.

    Returns
    -------
    A pd.Timestamp object (if successful), else None

    Raises
    ------
    TypeError
        Raises a type error if it encounters unsupported date types.

    """
    raise TypeError(
        f"Unsupported date format. You provided type: {type(date_input)}."
        "Supported types are FedStampConvertibleTypes"
    )


@to_timestamp.register(cls=pd.Timestamp)
def _timestamp_to_timestamp(date_input: Timestamp) -> Timestamp:
    """Conversion for pandas Timestamps"""
    return _normalize_timestamp(date_input)


@to_timestamp.register(cls=int)
@to_timestamp.register(cls=np.int64)
@to_timestamp.register(cls=float)
def _posix_to_timestamp(date_input: int | int64 | float) -> Timestamp:
    """
    Conversion for POSIX timestamps; we assume isolated integers or floats are
    POSIX time. Times less than 84,000 (almost a full day of
    second-based POSIX time) we assume are posix-days. Since the start of
    posix time is zero either way, we don't have to worry about this two hour
    period. We follow the pandas convention of terminating at year 2200 (84000
    posix-days is actually 2199-12-26, but it's round).
    """
    if (
        isinstance(date_input, np.int64) or date_input > 7_258_032_000
    ):  # year 2200 in epoch seconds
        return _normalize_timestamp(pd.to_datetime(date_input, unit="ns"))
    if date_input < 84000:
        return _normalize_timestamp(pd.to_datetime(date_input, unit="D"))
    return _normalize_timestamp(pd.to_datetime(date_input, unit="s"))


@to_timestamp.register(cls=str)
def _str_to_timestamp(date_input: str) -> Timestamp:
    """
    Conversion for string dates.
    If normal attempts fail, we try American date formats -- this being an
    American calendar -- and then European date formats.

    Raises
    ------
    ValueError
        raises a ValueError if it cannot parse a provided string.

    """
    try:
        return _normalize_timestamp(pd.to_datetime(date_input))
    except ValueError as e:
        for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                parsed_date: Timestamp = pd.to_datetime(date_input, format=fmt)
                return _normalize_timestamp(parsed_date)
            except ValueError:
                continue
        raise ValueError(
            f"Date string '{date_input}' is not in a recognized format. All "
            "reasonable attempts to parse it failed. Are you trying to use an "
            "alien date format? If you communicate in timelessness like those "
            "aliens in Arrival we're at an impasse. Please use an ISO 8601 "
            "format."
        ) from e


@to_timestamp.register(cls=datetime.date)
@to_timestamp.register(cls=datetime.datetime)
@to_timestamp.register(cls=np.datetime64)
def _date_to_timestamp(
    date_input: datetime.date | datetime.datetime | datetime64,
) -> Timestamp:
    """Conversions for Python date and datetime objects."""
    return _normalize_timestamp(date_input)


@to_timestamp.register(cls=tuple)
def _timetuple_to_timestamp(date_input: tuple) -> Timestamp:
    if len(date_input) != 3:
        raise ValueError(
            "Timetuple input requires a tuple with four-digit year, month, "
            "day as integers or integer-convertible strings."
        )
    try:
        year, month, day = (int(item) for item in date_input)
    except ValueError as e:
        raise ValueError(
            "Year, month, and day must be integers or strings that can be "
            "converted to integers."
        ) from e

    if not 1970 <= year <= 2200:
        raise ValueError("Year must be a four-digit number between 1970 and 2199")

    return _normalize_timestamp(pd.Timestamp(year=year, month=month, day=day))


def _check_year(dates: Timestamp | DatetimeIndex) -> Timestamp | DatetimeIndex:
    if isinstance(dates, pd.Timestamp):
        if 1969 < dates.year < 2200:
            return dates
        else:
            raise ValueError(
                "Input dates must be in range 1970-1-1 and 2199-12-31, you "
                f"provided a date from year {dates.year}."
            )

    if dates.year.min() > 1969 and dates.year.max() < 2200:
        return dates
    else:
        raise ValueError(
            "Input dates must be in range 1970-1-1 and 2199-12-31. "
            f"You provided dates in range {dates.year.min()}-{dates.year.max()}."
        )


@decorator
def check_timestamp(call) -> Timestamp | None:
    """
    Since _normalize_timestamp is designed to normalize Timestamps, to avoid
    repeating ourselves with conversions to Timestamps in most of our
    to_timestamp converters, we instead wrap/decorate _normalize_timestamp to
    intercept and convert any non-Timestamps to Timestamps once to_timestamp
    gets them in a format pd.Timestamp will accept.

    Parameters
    ----------
    func : Our wrapped function.

    Returns
    -------
    A wrapper around func that converts non-pd.Timestamp input to Timestamps.
    """
    arg = call._args[0]

    if isinstance(arg, pd.Timestamp):
        return call._func(_check_year(dates=arg))

    if arg is None:
        raise ValueError(
            f"provided argument, {arg} is None; we're not mind readers "
            "here. Please provide a pd.Timestamp for _normalize_timestamp."
        )

    try:
        ts = pd.Timestamp(arg)
        return call._func(_check_year(dates=ts))
    except TypeError as e:
        raise TypeError(
            f"input {arg} could not be converted to a pd.Timestamp. "
            "Our _normalize_timestamp function needs pandas Timestamps "
            "or a pd.Timestamp convertible date-like object (e.g. Python "
            "date, timetuple, string-date, POSIX)"
        ) from e


@check_timestamp
def _normalize_timestamp(timestamp: Timestamp | None = None) -> Timestamp:
    """
    If incoming Timestamps have timezone information, we normalize them to
    timezone naive UTC for consistency and because we're concerned with
    date-level precision here.

    Parameters
    ----------
    timestamp : A pandas pd.Timestamp for normalization

    Returns
    -------
    Normalized Timestamp

    """
    if timestamp.tzinfo:
        timestamp = timestamp.tz_convert(tz="UTC").normalize()
    return timestamp.normalize()


@decorator
def wrap_tuple(call) -> tuple[Any] | Any | None:
    """
    To avoid repeating ourselves with date converters that handle two
    arguments for FedIndex, we instead wrap the singledispatch
    function so it converts two arguments into a tuple. This way, we can
    elegantly route all tuples to our existing to_timestamp converters.

    wrap_tuple intercepts something like:
        to_datetimeindex(date1, date2)

    And forwards it on as:
        to_datetimeindex((date1, date2))

    Parameters
    ----------
    func : Our wrapped function.

    Returns
    -------
    A wrapper around func that converts multi-argument dates to a tuple.

    """
    args = call._args

    if len(args) == 1:
        return call._func(args[0])
    elif len(args) == 2:
        return call._func((args[0], args[1]))
    else:
        raise ValueError(f"Expected 1 or 2 arguments, got {len(args)}")


@wrap_tuple
@singledispatch
def to_datetimeindex(*input_dates: FedIndexConvertibleTypes) -> DatetimeIndex | None:
    """
    A singledispatch function for handling date conversions to DatetimeIndex.
    Most types are pushed into tuples by wrap_tuple and funneled to our
    to_datetime functions for conversion. We also add support for array_like
    objects, such as pandas pd.Index and pd.Series, and numpy ndarrays. And, of
    course, pd.DatetimeIndex itself.

    Like Timestamp, we do this to ensure they're normalized and to add finer
    control.

    Parameters
    ----------
    input_dates : Any FedIndexConvertibleTypes (i.e. any
    FedStampConvertibleType, pd.Timestamp).

    Returns
    -------
    A DatetimeIndex.

    Raises
    ------
    TypeError
        If supplies with an unsupported type.

    """

    raise TypeError(
        "You provided unsupported types. "
        "Supported types are FedIndexConvertibleTypes: \n"
        f"{FedIndexConvertibleTypes}"
    )


@to_datetimeindex.register(cls=tuple)
def _from_tuple(input_dates: tuple[Any]) -> DatetimeIndex:
    """
    We reuse `to_timestamp` to efficiently handle tuples of supported types.
    Even if not provided as a tuple, any two arguments will be funneled into
    a tuple by wrap_tuple.
    """
    start, end = map(to_timestamp, input_dates)
    return _get_datetimeindex_from_range(start=start, end=end)


@to_datetimeindex.register(cls=pd.DatetimeIndex)
def _from_datetimeindex(input_dates: DatetimeIndex) -> DatetimeIndex:
    """We catch and release DatetimeIndexes"""
    return _normalize_datetimeindex(datetimeindex=_check_year(dates=input_dates))


@to_datetimeindex.register(cls=pd.Series)
@to_datetimeindex.register(cls=pd.Index)
@to_datetimeindex.register(cls=np.ndarray)
def _from_array_like(input_dates: Series | Index | NDArray) -> DatetimeIndex:
    """
    We try to convert array-like objects to pd.DatetimeIndex

    Raises
    ------
    ValueError
        If the conversion fails, likely because the array does not contain
        datetimes.

    """
    try:
        datetimeindex = pd.DatetimeIndex(data=input_dates)
        return _normalize_datetimeindex(datetimeindex=_check_year(dates=datetimeindex))

    except ValueError as e:
        raise ValueError(
            f"""Failed to convert input to pd.DatetimeIndex. Must contain
            inputs compatible with a pandas pd.DatetimeIndex. You provided: \n
            {input_dates}"""
        ) from e


@to_datetimeindex.register(cls=pd.PeriodIndex)
def _from_periodindex(input_dates: PeriodIndex) -> DatetimeIndex:
    """
    Simple conversion routing for PeriodIndex.
    """
    return _normalize_datetimeindex(
        datetimeindex=_check_year(dates=input_dates.to_timestamp(freq="D"))
    )


def _get_datetimeindex_from_range(
    start: Timestamp | FedStampConvertibleTypes,
    end: Timestamp | FedStampConvertibleTypes,
) -> DatetimeIndex:
    """
    Converts a start and end date to datetimeindex.

    Parameters
    ----------
    start : The start date.
    end : The end date.

    Returns
    --------
    A datetimeindex.

    """
    start = start if isinstance(start, pd.Timestamp) else to_timestamp(start)
    end = end if isinstance(end, pd.Timestamp) else to_timestamp(end)

    datetimeindex: DatetimeIndex = pd.date_range(
        start=start, end=end, freq=to_offset(freq="D"), inclusive="both"
    )
    return _normalize_datetimeindex(datetimeindex=_check_year(dates=datetimeindex))


def _normalize_datetimeindex(datetimeindex: DatetimeIndex) -> DatetimeIndex:
    """
    Normalizes a datetimeindex to UTC and makes it timezone naive
    because we're not concerned with that kind of precision here,
    and it keeps output consistent.

    Parameters
    ----------
    datetimeindex : A pandas DatetimeIndex for normalization

    Returns
    -------
    A normalized DatetimeIndex

    """
    if datetimeindex.tz:
        return datetimeindex.tz_convert(tz="UTC").normalize()
    return datetimeindex.normalize()


__all__: list[str] = [
    "check_timestamp",
    "datetime_keys",
    "dt64_to_date",
    "dt64_to_dow",
    "ensure_datetimeindex",
    "find_datetime",
    "find_nearest",
    "get_today",
    "is_datetime_like",
    "iso_to_ts",
    "to_datetimeindex",
    "to_dt64",
    "to_timestamp",
    "ts_to_posix_day",
    "wrap_tuple",
]
