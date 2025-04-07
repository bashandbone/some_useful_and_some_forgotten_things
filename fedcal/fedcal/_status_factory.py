# fedcal _status_factory.py
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
This module replaces multiple modules in the previous back-end that employed
a complex series of interval trees, generators, and objects. Instead, we now
have a simple factory pipeline to reliably pipe our time series department
status data into fedcal using native pandas objects. It processes and returns
our data as a pandas MultiIndex layered by time-based Interval Index at the
top level (level-0), and string representations of and Dept and DeptStatus
objects on the next levels.)
"""
import json
from pathlib import Path

import pandas as pd
from pandas import MultiIndex, Timestamp

from fedcal._typing import RefinedIntervalType
from fedcal.enum import Dept, DeptStatus
from fedcal.utils import iso_to_ts

# set path to our JSON data as path to our module... plus filename, of course.
json_file_path: Path = Path(__file__).parent / "status_intervals.json"

cr_data_cutoff = pd.Timestamp(year=1998, month=10, day=1)

"""
cr_data_cutoff: The historical limit to continuing resolution data. We haven't
compiled the necessary data for statuses before this date.
Shutdowns and funding gaps, on the other hand, are compiled to the start of
the Epoch, 1970-1-1.
"""

dhs_formed = pd.Timestamp(year=2003, month=11, day=25)

"""
dhs_formed: Date of DHS formation
"""


def load_statuses() -> list[dict]:
    """
    Loads the status json.

    Returns
    -------
        A list of dictionaries from the json contents.
    """
    with open(file=json_file_path, mode="r") as f:
        data: list[dict[str, str]] = json.load(fp=f)
    return data


def process_interval(
    interval_data: dict[str, str],
) -> RefinedIntervalType:
    """
    Processes interval data from filter_intervals into Interval, Dept, and
    DeptStatus.

    Parameters
    ----------
    interval_data
        Raw or datetime-processed intervals

    Returns
    -------
    RefinedIntervalType; our intervals ready to load
    into an index
    """
    start: Timestamp = iso_to_ts(t=interval_data["interval"]["start"])
    end: Timestamp = iso_to_ts(t=interval_data["interval"]["end"])
    dept: Dept = Dept[interval_data["dept"]]
    status: DeptStatus = DeptStatus[interval_data["status"]]
    return (
        pd.Interval(left=start, right=end, closed="left"),
        dept.short,
        status.var,
    )


def to_multi_index(interval_list: list[RefinedIntervalType]) -> MultiIndex:
    """
    Converts our intervals to a MultiIndex.

    Parameters
    ----------
    interval_list
        list of tuples from process_interval

    Returns
    -------
    pd.MultiIndex with intervals, departments, and statuses as levels
    """
    intervals, depts, statuses = zip(*interval_list)
    return pd.MultiIndex.from_arrays(
        arrays=[intervals, depts, statuses], names=["Interval", "Department", "Status"]
    )


def fetch_index() -> MultiIndex:
    """
    Fetches intervals from status_intervals.json.

    TODO: Implement some kind of binary search to efficiently grab
    what we need. This isn't slow as-is, but it seems wasteful to load
    everything every time... when it could be just for, a Timestamp.

    Returns
    -------
    MultiIndex with intervals, departments, and statuses as levels
    """
    raw_intervals: list[dict[str, str]] = load_statuses()

    processed_intervals: list[RefinedIntervalType] = [
        process_interval(interval_data=i) for i in raw_intervals
    ]
    return to_multi_index(interval_list=processed_intervals)


__all__: list[str] = [
    "fetch_index",
    "load_statuses",
    "process_interval",
    "to_multi_index",
]
