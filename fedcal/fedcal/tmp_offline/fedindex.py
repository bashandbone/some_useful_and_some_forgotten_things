# fedcal fedindex.py
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
fedindex is one of fedcal's main APIs, home to `FedIndex` a proxy
for pandas' `pd.DatetimeIndex` with additional functionality for fedcal
data, with the goal of seamlessly building on `pd.DatetimeIndex` and
integrating fedcal data into pandas analyses.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from numpy import int64
from numpy.typing import NDArray
from pandas import (
    DataFrame,
    DatetimeIndex,
    Index,
    MultiIndex,
    PeriodIndex,
    Series,
    Timestamp,
)

from fedcal import utils
from fedcal._base import MagicDelegator
from fedcal._status_factory import fetch_index
from fedcal._typing import FedIndexConvertibleTypes, FedStampConvertibleTypes
from fedcal.enum import Dept, DeptStatus, depts_set
from fedcal.fiscal import FedFiscalCal
from fedcal.offsets import (
    FedBusinessDay,
    FedHolidays,
    FedPayDay,
    MilitaryPassDay,
    MilitaryPayDay,
)


class FedIndex(
    metaclass=MagicDelegator,
    delegate_to="datetimeindex",
    delegate_class=pd.DatetimeIndex,
):

    """
    `FedIndex` extends pd.DatetimeIndex with additional
    functionality specific to federal dates. Like `FedStamp`, it uses
    a metaclass, `MagicDelegator`, combined with attribute delegation to its
    datetimeindex attribute to mirror pandas' `DatetimeIndex` functionality
    while adding significant additional capabilities for federal analysis.It
    includes methods and properties for handling various aspects of federal
    operations, such as paydays, department statuses, and fiscal years.

    Attributes
    ----------
    posix_day
        Converts dates to a numpy array of POSIX-day timestamps.

    business_days : Series
        pd.Series indicating business days.

    fys : Series
        pd.Series representing fiscal years.

    fqs : Series
        pd.Series for fiscal quarters.

    holidays : Series
        pd.Series indicating holidays.

    proclaimed_holidays : NDArray
        Array of boolean values for proclaimed holidays.

    possible_proclamation_holidays : NDArray
        Array of boolean values for possible proclamation holidays.

    probable_mil_passdays : Series
        pd.Series indicating probable military pass days.

    mil_paydays : Series
        pd.Series of military paydays.

    civ_paydays : Series
        pd.Series of civilian paydays.

    departments : DataFrame
        pd.DataFrame of departments.

    departments_bool : DataFrame
        pd.DataFrame indicating department existence per date.

    all_depts_status : DataFrame
        pd.DataFrame with status for all departments.

    all_depts_full_approps : Series
        pd.Series for departments with full appropriations.

    all_depts_cr : Series
        pd.Series for departments under a continuing resolution.

    all_depts_funded : Series
        pd.Series for departments under full appropriations or a CR.

    all_depts_unfunded : Series
        pd.Series for all unfunded departments.

    gov_cr : Series
        pd.Series indicating any department under a CR.

    gov_shutdown : Series
        pd.Series indicating any department in a shutdown.

    gov_unfunded : Series
        pd.Series for any unfunded department.

    full_op_depts : DataFrame
        pd.DataFrame of fully operational departments.

    funded_depts : DataFrame
        pd.DataFrame of departments fully funded or under a CR.

    cr_depts : DataFrame
        pd.DataFrame of departments under a CR.

    gapped_depts : DataFrame
        pd.DataFrame of departments in a funding gap.

    shutdown_depts : DataFrame
        pd.DataFrame of departments in a shutdown.

    unfunded_depts : DataFrame
        pd.DataFrame of unfunded departments.

    Methods
    -------

    contains_date
        Checks if a date is in the index.

    contains_index
        Checks if another index is contained within this one.

    overlaps_index
        Checks for any overlap with another index.

    construct_status_dataframe
        Constructs a status pd.DataFrame based on given criteria.

    status_dataframe_to_multiindex
        Converts a status pd.DataFrame to a multiindex pd.DataFrame.

    status_dataframe_to_all_bool
        Converts a status pd.DataFrame to a boolean pd.DataFrame.

    get_departments_status
        Retrieves the status of specified departments.

    Examples
    --------
    # Example usage
    (TODO: Beef up examples)
    fed_index = FedIndex(['2023-01-01', '2023-01-02'])
    print(fed_index.business_days)
    print(fed_index.full_op_depts)

    Notes
    -------
    *Private Methods*:
        _reverse_human_readable_status : Converts human-readable status to
        internal representation.
        set_self_date_range : Sets the start and end date of the index.
        _get_mil_cache : Retrieves military cache data.
        _set_mil_cache : Sets the military cache.
        _set_status_gen : Sets the status generator.
        _get_status_gen : Gets the status generator.
        _set_status_cache : Sets the status cache.
        _generate_status_cache : Generates the status cache.
        _extract_status_data : Extracts status data based on filters.
        _check_dept_status : Checks department status against criteria.
        _set_holidays : Sets the _holidays attribute once needed.

    TODO
    ----
    Implement new status system into methods

    Implement custom __setattr__, __setstate_cython__, __setstate__,
    __init_subclass__, __hash__, __getstate__, __dir__, (__slots__?)
    """

    def __init__(
        self,
        datetimeindex: DatetimeIndex | None = None,
        dates: FedIndexConvertibleTypes | None = None,
    ) -> None:
        if isinstance(datetimeindex, pd.DatetimeIndex):
            self.datetimeindex: DatetimeIndex = datetimeindex
        elif datetimeindex or dates:
            self.datetimeindex = self._convert_input(
                time_input=datetimeindex
            ) or self._convert_input(time_input=dates)
        else:
            self.datetimeindex: DatetimeIndex = self._set_default_index()
        self.start: Timestamp
        self.end: Timestamp
        self.start, self.end = self.set_self_date_range()

        # define caches; only created if accessed
        self._holidays: FedHolidays | None = None
        self._fiscalcal: FedFiscalCal = None

    def __getattr__(self, name: str) -> Any:
        """
        We delegate attribute access to `FedIndex`'s datetimeindex
        attribute, which helps with the magic of making `FedIndex`
        objects behave well with pandas.

        Parameters
        ----------
        name
            name of the attribute being fetched.

        Returns
        -------
            attribute if found, either in `FedIndex`'s dict or
            in pd.DatetimeIndex.

        Raises
        ------
        AttributeError
            if attribute can't be found
        """
        # this shouldn't be necessary, but...
        # seems to be until I can work out why
        if name in type(self).__dict__:
            return type(self).__dict__[name].__get__(self, type(self))

        if hasattr(self.datetimeindex, name):
            return getattr(self.datetimeindex, name)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getattribute__(self, name: str) -> Any:
        """
        We manually set __getattribute__ to ensure `FedIndex`'s
        attribute retrievals are handled properly and not overridden
        by our metaclass or attribute delegation to `pd.DatetimeIndex`.

        Parameters
        ----------
        name
            name of attribute to get

        Returns
        -------
            attribute if found
        """
        return object.__getattribute__(self, name)

    # Methods for caching and other internal use to the class
    @staticmethod
    def _convert_input(time_input: FedIndexConvertibleTypes) -> DatetimeIndex:
        """
        Routes input to converter methods in utils module for
        conversion and normalization.

        Parameters
        ----------
        time_input
            any FedIndexConvertibleTypes date range input

        Returns
        -------
            a pd.DatetimeIndex object for self.datetimeindex
        """
        return utils.to_datetimeindex(time_input)

    @staticmethod
    def _set_default_index() -> DatetimeIndex:
        """
        Sets the default index range if no date input is provided

        Returns
        -------
            `pd.DatetimeIndex` with default range of FY99 to FY44.
        """
        default_range: tuple[Timestamp, Timestamp] = pd.Timestamp(year=1998,month=10,day=1), pd.Timestamp(year=2045,month=9,day=30)
        return utils.to_datetimeindex(default_range)

    def set_self_date_range(self) -> tuple[Timestamp, Timestamp]:
        """
        Set the start and end date range of the FedIndex instance.

        Notes
        -----
        This method sets the `start` and `end` attributes of the instance It
        defaults to the minimum and maximum of the index if `start` or `end`
        are not explicitly set.
        """
        return self.datetimeindex.min(), self.datetimeindex.max()

    # utility methods

    def contains_date(self, date: FedStampConvertibleTypes) -> bool:
        """
        Check if the index contains a specified date.

        Parameters
        ----------
        date : FedStampConvertibleTypes
        The date to check for in the index.

        Returns
        -------
        bool
        True if the date is in the index, False otherwise.

        Notes
        -----
        This method converts the input date to a `FedStamp`, if necessary,
        and then checks if it exists in the index.
        """
        date: Timestamp = utils.to_timestamp(date)
        return date in self.datetimeindex

    def contains_index(self, other_index: FedIndexConvertibleTypes) -> bool:
        """
        Check if the index wholly contains another index..

        Parameters
        ----------
        other_index : FedIndexConvertibleTypes
            The other index to check for containment.

        Returns
        -------
        bool
            True if the other index is wholly contained in this index, False
            otherwise.
        """
        other_index = (
            other_index.datetimeindex
            if isinstance(other_index, FedIndex)
            else utils.to_datetimeindex(other_index)
        )
        return other_index.isin(values=self.datetimeindex).all()

    def overlaps_index(self, other_index: "FedIndexConvertibleTypes") -> bool:
        """
        Check if the index overlaps with another index.

        Parameters
        ----------
        other_index : FedIndexConvertibleTypes
            The other index to check for overlap.

        Returns
        -------
        bool
            True if any date from the other index is in this index, False
            otherwise.

        Notes
        -----
        This method converts the input index, if
        necessary, and then checks for any overlapping dates using the `isin`
        method.
        """
        other_index = (
            other_index.datetimeindex
            if isinstance(other_index, FedIndex)
            else utils.to_datetimeindex(other_index)
        )
        return other_index.isin(values=self.datetimeindex).any()

    def _set_fiscalcal(self) -> None:
        """
        Sets the _fiscalcal attribute for fy/fq retrievals.
        """
        if not hasattr(FedFiscalCal, "fqs") or not self._fiscalcal:
            self._fiscalcal: FedFiscalCal = FedFiscalCal(dates=self.datetimeindex)

    def _set_holidays(self) -> None:
        """
        Sets the self._holidays attribute for FedHolidays retrievals.
        """
        if not self._holidays:
            self._holidays: FedHolidays = FedHolidays()

    # Begin date attribute property methods
    @property
    def posix_day(self) -> NDArray[int64]:
        """
        Convert the dates in the index to POSIX-day timestamps normalized to
        midnight.

        Returns
        -------
        ndarray
            A numpy array of integer POSIX-day timestamps.

        Notes
        -----
        This method normalizes each date in the index to midnight and then
        converts them to POSIX-day timestamps (seconds since the Unix epoch).
        """
        return self.datetimeindex.normalize().asi8 // (24 * 60 * 60 * 1_000_000_000)

    @property
    def business_days(
        self,
    ) -> NDArray[bool]:
        """
        Determine if the dates in the index are Federal business days
        (adjusted for holidays).

        Returns
        -------
        numpy ndarray of boolean values, True on businessdays
        """
        return FedBusinessDay().is_on_offset(dt=self.datetimeindex)

    @property
    def fys(self) -> Index[int]:
        """
        Retrieve the fiscal years for each date in the index.

        This property maps each date in the index to its corresponding federal
        fiscal year.

        Returns
        -------
        pd.Index
            A Pandas pd.Index with the fiscal year for each date in the index.

        """
        self._set_fiscalcal()
        return self._fiscalcal.fys

    @property
    def fqs(self) -> Index[int]:
        """
        Obtain the fiscal quarters for each date in the index.

        This property identifies the federal fiscal quarter for each date in
        the index.

        Returns
        -------
        pd.Index
            A Pandas pd.Index with the fiscal quarter for each date in the
            index.

        """
        self._set_fiscalcal()
        return self._fiscalcal.fqs

    @property
    def fys_fqs(self) -> PeriodIndex:
        """
        Retrieve the fiscal year and quarter for each date in the index.

        This property identifies the federal fiscal year and quarter for each
        date in the index in string format 'YYYYQ#'

        Returns
        -------
        pd.PeriodIndex
            A Pandas pd.PeriodIndex with the fiscal year-quarter for each date
            in the index.

        """
        self._set_fiscalcal()
        return self._fiscalcal.fys_fqs

    @property
    def fq_start(self) -> PeriodIndex:
        """
        Identify the first day of each fiscal quarter.

        This property identifies the first day of each fiscal quarter in
        the index.

        Returns
        -------
        pd.PeriodIndex
            Returns an index of quarter start dates within the range.
        """
        self._set_fiscalcal()
        return self._fiscalcal.fq_start

    @property
    def fq_end(self) -> PeriodIndex:
        """
        Identify the last day of each fiscal quarter.

        This property identifies the last day of each fiscal quarter in the
        index.

        Returns
        -------
        pd.PeriodIndex
            Returns an index of quarter end dates within the range.
        """
        self._set_fiscalcal()
        return self._fiscalcal.fq_end

    @property
    def fy_start(self) -> PeriodIndex:
        """
        Identify the first day of each fiscal year.

        This property identifies the first day of each fiscal year in the
        index.

        Returns
        -------
        pd.PeriodIndex
            Returns an index of year start dates within the range.
        """
        self._set_fiscalcal()
        return self._fiscalcal.fy_start

    @property
    def fy_end(self) -> PeriodIndex:
        """
        Identify the last day of each fiscal year.

        This property identifies the last day of each fiscal year in the
        index.

        Returns
        -------
        pd.PeriodIndex
            Returns an index of year end dates within the range.
        """
        self._set_fiscalcal()
        return self._fiscalcal.fy_end

    @property
    def holidays(self) -> DatetimeIndex:
        """
        Identify federal holidays in the index.

        Returns
        -------
        DatetimeIndex
            DatetimeIndex reflecting dates of holidays
        """
        self._set_holidays()
        return self.datetimeindex.isin(values=self._holidays.np_holidays)

    @property
    def proclaimed_holidays(self) -> DatetimeIndex:
        """
        Check for proclaimed federal holidays in the index.

        This property identifies dates in the index that are (historical)
        proclaimed federal holidays.

        Returns
        -------
        boolean NDArray, True on proclaimed holidays.
        """
        self._set_holidays()
        return self.datetimeindex.isin(values=self._holidays.proclaimed_holidays)

    @property
    def future_proclamation_holiday_estimate(self) -> Series[float] | DataFrame:
        """
        Estimates probability if the dates in the index are possible *future*
        proclamation federal holidays based on frequency of past proclamations
        for that day of week relative to the Christmas holiday.

        Importantly, only Christmas Eves or their observed equivalents have any
        probability, and only future dates are calculated. All but two
        historical proclamation holidays were Christmas Eves, with the other
        two, a day after Christmas and a New Years Eve, not providing
        sufficient data to attempt an estimate.

        Returns
        -------
        A series of float probabilities for future Christmas Eve holiday
        proclamations.

        Notes
        -----
        If you're curious -- odds are good if Christmas is on a Tuesday,
        otherwise it's hit or miss.

        """
        self._set_holidays()
        return self._holidays.estimate_future_proclamation_holidays(
            future_dates=self.datetimeindex
        )

    @property
    def mil_passdays(self, custom_dow_map: dict[str, str] = None) -> NDArray[bool]:
        """
        Identify likely business days that will be military passdays based
        on an adjacent holiday.

        Some important caveats:
        1) Passdays can be highly variable to locale and command
        2) While passes technically covering a longer period, usually a
        weekend, here we only concern ourselves with impacted business days as
        the anomaly from the norm.
        3) Default behavior puts passdays on Friday if the holiday is a Monday
        or Thursday, on Monday if the holiday is a Tuesday or Friday, and on
        Thursday if the holiday is a Wednesday. Wednesday is the most likely
        to vary but also the least common situation. You may pass a custom day
        of week map within constraints to calculate alternate behavior (see
        MilitaryPassDay docs for details.)

        Returns
        -------
        NDArray of booleans, True on probable passdays.
        """

        return MilitaryPassDay(passday_map=custom_dow_map).is_on_offset(
            dt=self.datetimeindex
        )

    # Payday properties
    @property
    def mil_paydays(self) -> NDArray[bool]:
        """
        Identify military payday dates within the index.

        This property uses the index's date range and MilitaryPayDay object to
        determine the dates that are military paydays.

        Returns
        -------
        DatetimeIndex
            A datetimeindex reflecting military payday dates.
        """
        return MilitaryPayDay().is_on_offset(dt=self.datetimeindex)

    @property
    def civ_paydays(self) -> NDArray[bool]:
        """
        Determine civilian payday dates within the index's date range.

        Identifies federal biweekly civilian paydays within the range.

        Returns
        -------
        NDArray of booleans, True on paydays.
        """

        self.set_self_date_range()
        return FedPayDay().is_on_offset(dt=self.datetimeindex)

    @property
    def departments(self) -> DataFrame:
        """
        Create a pd.DataFrame of departments active on each date in the index.

        This property generates a pd.DataFrame where each row corresponds to a
        date in the index, listing the active executive departments on that
        date and adjusting for the formation of DHS.

        Returns
        -------
        pd.DataFrame
            A pd.DataFrame with each date in the index and the active
            departments
            on that date.
        """
        pass

    @property
    def departments_bool(self) -> DataFrame:
        """
        Generates a pd.DataFrame indicating whether each department exists on
        each date in the index.

        This method specifically accounts for the formation of the
        Department of Homeland Security (DHS). Dates prior to DHS's
        formation will have a False value for DHS.

        Returns
        -------
        pd.DataFrame
            A pd.DataFrame with the index as dates and columns as department
            short names. Each cell is True if the department exists on that
            date, except for DHS before its formation date, which is False.
        """

        pass

    @staticmethod
    def get_status_keys() ->


def to_fedindex(*dates: FedIndexConvertibleTypes) -> FedIndex:
    """
    Converts a date range to a `FedIndex`.

    Parameters
    ----------
    date_range
        A date range to convert to a `FedIndex`. The date range can be any
        `FedIndexConvertibleTypes`:
            tuple[FedStampConvertibleTypes, FedStampConvertibleTypes],
            tuple[pd.Timestamp, pd.Timestamp],
            NDArray,
            "pd.Series",
            "pd.DatetimeIndex",
            "pd.Index",
        ]

    Returns
    -------
    FedIndex
        A `FedIndex` object representing the date range.

    Examples
    --------
    ```python
    to_fedindex((("2017-10-1"), "2025-9-30"))
    to_fedindex(pd.date_range(start="2017-10-1", end="2025-9-30"))
    to_fedindex(np.arange("2017-10-1", "2025-9-30", dtype="datetime64[D]"))
    to_fedindex(pd.Series(pd.date_range(start="2017-10-1", end="2025-9-30")))
    to_fedindex(pd.Index(pd.date_range(start="2017-10-1", end="2025-9-30")))
    to_fedindex(((datetime.datetime(2000,1,1)),datetime.datetime(2010,5,30)))
    ```
    """
    if count := len(dates):
        if count in {1, 2}:
            return FedIndex(datetimeindex=utils.to_datetimeindex(dates))
    raise ValueError(
        f"Invalid number of arguments: {count}. Please pass either an "
        "array-like date object or start and end dates for the range."
    )
