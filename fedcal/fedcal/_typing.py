# fedcal _typing.py
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
This module provides internal type definitions for fedcal to keep the code
clean but well-typed.
"""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, TypeVar, Union

from numpy import datetime64, int64
from numpy.typing import NDArray
from pandas import DatetimeIndex, Index, Interval, PeriodIndex, Series, Timestamp

if TYPE_CHECKING:
    from fedcal.enum import EnumBase

TimestampSeries = "Series[Timestamp]"

EnumType = TypeVar("EnumType", bound="EnumBase")

FedStampConvertibleTypes = Union[
    Timestamp,
    int,
    int64,
    datetime64,
    float,
    tuple[int, int, int],
    tuple[str, str, str],
    str,
    datetime.date,
    datetime.datetime,
]

FedIndexConvertibleTypes = Union[
    tuple[FedStampConvertibleTypes, FedStampConvertibleTypes],
    tuple[Timestamp, Timestamp],
    NDArray[datetime64],
    TimestampSeries,
    DatetimeIndex,
    Index,
    PeriodIndex,
]

RefinedIntervalType = tuple[Interval, "Dept", "DeptStatus"]

DatetimeScalarOrArray = Union[
    datetime,
    datetime.date,
    datetime64,
    Timestamp,
    int64,
    DatetimeIndex,
    TimestampSeries,
    NDArray[datetime64 | int64],
]

__all__: list[str] = [
    "DatetimeScalarOrArray",
    "EnumType",
    "FedIndexConvertibleTypes",
    "FedStampConvertibleTypes",
    "RefinedIntervalType",
    "TimestampSeries",
]
