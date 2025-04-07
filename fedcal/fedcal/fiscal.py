# fedcal fiscal.py
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
The fiscal module consists of the FedFiscalCal class, which
computes and exports Federal fiscal years and quarters and related timeseries
data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pandas import DatetimeIndex, Index, PeriodIndex, Series, Timestamp

from fedcal._typing import TimestampSeries
from fedcal.utils import ensure_datetimeindex, to_datetimeindex


@dataclass(order=True, slots=True)
class FedFiscalCal:
    """
    Class representing the federal fiscal year calculations.

    Attributes
    ----------
    dates : Reference dates for fiscal year calculations.

    fys_fqs : PeriodIndex of fiscal years and quarters in 'YYYYQ#' format.

    fys : Index of fiscal years as integers

    fqs : Index of fiscal quarters as integers

    fq_start : start day of fiscal quarters

    fq_end : end day of fiscal quarters

    fy_start : start day of fiscal years

    fy_end : end day of fiscal years

    Notes
    -----
    *Private Methods*:
    - _get_cal(dates)
        gets a tuple of the class attributes, fys_fqs, fys, and fqs. Used for
        setting instance attrs.
    - _get_fq_start_end()
        gets a tuple of the class attributes, fq_start, and fq_end. Used for
        setting instance attrs.
    - _get_fy_start_end()
        gets a tuple of the class attributes, fy_start, and fy_end. Used for
        setting instance attrs.
    """

    dates: DatetimeIndex | TimestampSeries | Timestamp | None = field(
        default=to_datetimeindex((1970, 1, 1), (2199, 12, 31))
    )

    fys_fqs: PeriodIndex | None = field(default=None, init=False)

    fys: Index[int] | None = field(default=None, init=False)

    fqs: Index[int] | None = field(default=None, init=False)

    fq_start: PeriodIndex | None = field(default=None, init=False)

    fq_end: PeriodIndex | None = field(default=None, init=False)

    fy_start: PeriodIndex | None = field(default=None, init=False)

    fy_end: PeriodIndex | None = field(default=None, init=False)

    def __attrs_post_init__(
        self, dates: DatetimeIndex | TimestampSeries | Timestamp | None = None
    ) -> None:
        """
        Complete initialization of the instance and sets attributes
        """
        self.dates = dates or self.dates
        self.fys_fqs, self.fys, self.fqs = self._get_cal()
        self.fq_start, self.fq_end = self._get_fq_start_end()
        self.fy_start, self.fy_end = self._get_fy_start_end()

    def _get_cal(
        self,
        dates: DatetimeIndex | TimestampSeries | Timestamp | None = None,
    ) -> tuple[PeriodIndex, Series[int], Series[int]]:
        """
        Calculate the fiscal year for each date in datetimeindex.

        Parameters
        ----------
        dates = dates for processing, else uses self.dates

        Returns
        -------
        A tuple of the class attributes, fys_fqs, fys, and fqs.
        """
        dates = ensure_datetimeindex(dt=dates) or self.dates

        fy_fq_idx: PeriodIndex = dates.to_period(freq="Q-SEP")

        fys: Index[int] = fy_fq_idx.qyear
        fqs: Index[int] = fy_fq_idx.quarter
        return fy_fq_idx, fys, fqs

    def _get_fq_start_end(self) -> tuple[PeriodIndex, PeriodIndex]:
        """
        Calculate the start and end dates of each fiscal quarter.

        Returns
        -------
        A tuple of the class attributes, fq_start, and fq_end as PeriodIndexes.
        """
        return self.fys_fqs.asfreq(freq="D", how="S"), self.fys_fqs.asfreq(
            freq="D", how="E"
        )

    def _get_fy_start_end(self) -> tuple[PeriodIndex, PeriodIndex]:
        """
        Calculate the start and end dates of each fiscal year.

        Returns
        -------
        A tuple of two PeriodIndexes: fy_start and fy_end.
        """
        fy_start: DatetimeIndex = self.fys_fqs[self.fys_fqs.quarter == 1].asfreq(
            "D", how="start"
        )
        fy_end: DatetimeIndex = self.fys_fqs[self.fys_fqs.quarter == 4].asfreq(
            "D", how="end"
        )

        return fy_start, fy_end


__all__: list[str] = ["FedFiscalCal"]
