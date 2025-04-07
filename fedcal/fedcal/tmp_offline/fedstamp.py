# fedcal fedstamp.py
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
fedstamp is one of fedcal's two main APIs, home to `FedStamp` a proxy
for pandas' `pd.Timestamp` with additional functionality for fedcal
data, with the goal of seamlessly building on `pd.Timestamp` and
integrating fedcal data into pandas analyses.
"""
from __future__ import annotations

from typing import Any, ClassVar

import pandas as pd
from pandas import MultiIndex, Timestamp

from fedcal._base import MagicDelegator
from fedcal.enum import Dept, DeptStatus
from fedcal._status_factory import fetch_index
from fedcal._typing import FedStampConvertibleTypes
from fedcal.fiscal import FedFiscalCal
from fedcal.offsets import (
    FedBusinessDay,
    FedHolidays,
    FedPayDay,
    MilitaryPassDay,
    MilitaryPayDay,
)
from fedcal.utils import to_timestamp, ts_to_posix_day


class FedStamp(metaclass=MagicDelegator, delegate_to="ts", delegate_class=pd.Timestamp):

    """
    `FedStamp` extends `pd.Timestamp` for fedcal functionality.
    Supports all functionalities of pandas' pd.Timestamp
    objects, while adding specific features for the fedcal.

    Attributes
    ----------
    ts : the `pd.Timestamp` object that forms the backbone of the
    instance. If a ts is not provided at instantiations, the
    instance will default to the current date (datetime.now()). Note: we
    use ts as an attribute name to avoid overwriting Timestamp.
    timestamp().

    _status_cache : A *private* lazy attribute that caches StatusDictType
    dictionary (Dict[Dept, FedDepartment]) from _dept_status.
    DepartmentState for the date for supplying status-related properties.
    Provided by _get_status_cache() and _set_status_cache() private
    methods.

    _holidays: A *private* lazy attribute that caches our FedHolidays
    instance once called.

    _fiscalcal: A *private* lazy attribute that caches our FiscalCalendar
    instance once called.

    posix_day
        Returns the POSIX-day timestamp normalized to midnight.

    business_day
        Checks if the date is a business day.

    holiday
        Checks if the date is a federal holiday.

    proclamation_holiday
        Checks if the date was a proclaimed holiday (i.e. a one-off holiday
        proclaimed by executive order).

    possible_proclamation_holiday
        Guesses (I take no further ownership of the result) if the future date
        will likely to be a proclaimed holiday.

    probable_military_passday
        Estimates if the date is likely a military pass day. Actual
        passdays vary across commands and locations, but this should
        return a result that's correct in the majority of cases.

    mil_payday
        Checks if the date is a military payday.

    civ_payday
        Checks if the date is a civilian payday.

    fq
        Retrieves the [Federal] fiscal quarter of the timestamp as 1-digit
        integer

    fy
        Retrieves the [Federal] fiscal year of the timestamp as 4-digit
        integer/

    fy_fq
        Retrieves the [Federal] fiscal year and fiscal quarter of the
        timestamp as a string in format 'YYYYQ#'.

    is_ffq_start
        Returns True if the Timestamp represents the first day of a fiscal
        quarter

    is_ffq_end
        Returns True if the Timestamp represents the last day of a fiscal
        quarter

    is_fy_start
        Returns True if the Timestamp represents the first day of a
        fiscal year

    is_fy_end
        Returns True if the Timestamp represents the last day of a
        fiscal year

    departments
        Retrieves the set of executive departments active on the date, as
        Dept enum objects.

    all_depts_status
        Retrieves the status of all departments as a dictionary on the
        date.

    all_depts_full_approps
        Checks if all departments are fully appropriated on the date,
        returning bool.

    all_depts_cr
        Checks if all departments were/are under a continuing resolution on
        the date, returning bool.

    all_depts_funded
        Checks if all departments were/are either fully appropriated or
        under a continuing resolution on the date, returning bool.

    all_unfunded
        Checks if all departments were/are unfunded on the date (either
        shutdown or otherwise gapped), returning bool.

    gov_cr
        Checks if the date was during a continuing resolution (can include
        near-future dates since we know CR expiration dates at the time
        they are passed), returning bool any departments were under a CR.

    gov_shutdown
        Checks if the date was/is during a shutdown, returning bool if any
        departments were shutdown.

    gov_approps_gap
        Checks if the date was/is during an appropriations gap, returning
        bool if any department had a gap in funding.

    gov_approps_gap
        Check if the date was/is during a funding gap (appropriations gap
        or shutdown), returning bool if any department was shutdown or
        had an appropriations gap

    full_op_depts
        Retrieves departments that were fully operational (had a full-year
        appropriation) on the date, returning a dict.

    funded_depts
        Retrieves departments that were/are either fully operational or
        under a continuing resolution on the date, returning a dict.

    cr_depts
        Retrieves departments that were/are under a continuing resolution
        on the date, returning a dict. Current data are from FY99 to
        present. As discussed above for cr, these can include near future
        dates.

    gapped_depts
        Retrieves departments that were/are in an appropriations gap on the
        date but not shutdown, returning a dict. Notably, these are
        isolated to the 1970s and early 80s.

    shutdown_depts
        Retrieves departments that were/are shut down on the date. Data
        available from FY75 to present.

    unfunded_depts
        Retrieves departments that were/are unfunded on the date (either
        gapped or shutdown), returning a dict.

    Methods
    -------
    dict_to_dept_set(status_dict)
        Converts a StatusDictType dictionary to a set of Dept
        enum objects.

    dict_to_feddept_set(status_dict)
        Converts a StatusDictType dictionary to a set of FedDepartment

    dict_to_dept_list(status_dict)
        Utility method that converts a status dictionary (which most of the
        status-related property methods return) to a sorted list of
        Dept enum objects.

    dict_to_feddept_list(status_dict)
        Utility method that converts a status dictionary (which most of the
        status-related property methods return) to a sorted list of
        FedDepartment objects.

    get_departments_by_status(status_key)
        Retrieves departments matching a specific status, primary getter
        for status-related property methods.

    Notes
    -----
    *Private Methods*:
    _set_statuses()
        a method to set the ClassVar `statuses`.

    _set_holidays()
        sets the _holidays attribute for the holiday, proclamation_holiday
        and possible_proclamation_holiday properties.

    _set_fiscalcal()
        sets the _fiscalcal attribute for the fiscal_quarter and fy
        related property methods


    TODO
    ----
    Implement new status system into methods


    Implement custom __setattr__, __setstate_cython__, __setstate__,
    __delattr__, __init_subclass__, __hash__, __getstate__, __dir__,
    __reduce__, __reduce_ex__, reduce_cython__, (__slots__?)
    """

    statuses: ClassVar[MultiIndex | None] = None

    def __init__(self, ts: Timestamp | None = None) -> None:
        """
        Initializes instance and sets ts to today if no ts
        provided at instantiation.

        Parameters
        ----------
        ts
            pd.Timestamp object to set as the ts. If not provided, the
            instance will default to the current date (datetime.now()).
            All core functionality of the class is built from this attribute.
        """
        if isinstance(ts, pd.Timestamp):
            self.ts: Timestamp = ts
        elif ts is not None:
            self.ts = to_timestamp(ts)
        else:
            pd.Timestamp.utcnow().normalize()

        self._holidays: FedHolidays | None = None
        self._fiscalcal: FedFiscalCal | None = None

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
        # this shouldn't be necessary...
        # but... it seems to be until I can work out why.
        if name in self.__class__.__dict__:
            return self.__class__.__dict__[name].__get__(self, self.__class__)

        if hasattr(self.ts, name):
            return getattr(self.ts, name)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getattribute__(self, name: str) -> Any:
        """
        We set __getattribute__ manually to ensure it overrides
        any delegation to pd.Timestamp from our metaclass.
        (It shouldn't, I know, but I swear it was.)

        Parameters
        ----------
        name
            name of attribute

        Returns
        -------
            attribute if found.
        """
        return object.__getattribute__(self, name)

    # static utility methods

    # utility properties
    @property
    def posix_day(self) -> int:
        """
        Built for internal use in fedcal, variation of pd.Timestamp.timestamp()
        method, which remains available. Returns the number of days since
        the Unix epoch (1970-01-01 00:00:00 UTC) as an integer normalized to
        midnight (vice pandas' return of a float).

        Returns
        -------
        Integer POSIX-day timestamp in seconds.

        """
        return ts_to_posix_day(timestamp=self.ts)

    # business day property
    @property
    def business_day(self) -> bool:
        """
        Checks if the date is a [Federal] business day.

        Returns
        -------
        True if the date is a business day, False otherwise.

        """
        b_day: FedBusinessDay = FedBusinessDay()
        return b_day.is_on_offset(dt=self.ts)

    # instance cache
    def _set_holidays(self) -> None:
        """
        Sets the holidays attribute.
        """
        if not hasattr(FedHolidays, "holidays") or self._holidays is None:
            self._holidays = FedHolidays()

    def _set_fiscalcal(self) -> None:
        """
        Sets the fiscalcal attribute.
        """
        if not hasattr(FedFiscalCal, "fqs") or self._fiscalcal is None:
            self._fiscalcal: FedFiscalCal = FedFiscalCal(dates=self.ts)

    @classmethod
    def _set_statuses(cls) -> None:
        """
        Sets the status cache if not already set.
        """
        if not hasattr(cls, "statuses"):
            cls.statuses: MultiIndex = fetch_index()

    # holiday properties
    @property
    def holiday(self, return_name: bool = False) -> bool | str:
        """
        Checks if the date is a federal holiday.

        Parameters
        ----------
        return_name : if true, returns the name of the holiday if
        a holiday, else false

        Returns
        -------
        True if the date is a federal holiday, False otherwise. If return_name
        flag is True, instead returns the name of the holiday if the day is a
        holiday.

        Notes
        -----
        This property is built on pandas' USFederalHolidayCalendar, but
        supplemented with historical holidays proclaimed by the President
        from FY74 to present (no known examples before that year).

        """
        self._set_holidays()
        series = self._holidays.holidays(
            start=(self.ts - pd.Timedelta(days=1)),
            end=(self.ts + pd.Timedelta(days=1)),
            return_name=return_name,
        )
        if return_name and self.ts in series:
            return series.at[self.ts, 0]
        return self.ts in series

    @property
    def proclamation_holiday(self, return_name=False) -> bool:
        """
        Checks if the date was an out-of-cycle holiday proclaimed by executive
        order. Data available from FY74 to present (no known instances before
        that time).

        Parameters
        ----------
        return_name : if true, returns the name of the holiday if a holiday,
        else false. Default is false.

        Returns
        -------
        True if the ts was a proclaimed holiday, False otherwise.

        """
        self._set_holidays()
        if return_name and self.ts in self._holidays.proclaimed_holidays:
            return self._holidays.proclamation_holidays(
                start=self.ts - pd.Timedelta(day=1),
                end=self.ts + pd.Timedelta(days=1),
                return_name=return_name,
            )
        return self.ts in self._holidays.proclaimed_holidays

    @property
    def future_proclamation_holiday_estimate(self) -> float:
        """
        If given a future date, estimate probability if it may be a proclaimed
        holiday. Uses the small sample of past proclaimed holidays to estimate
        the probability based on the day of the week. Only checks Christmas
        Eves (or business day prior to Christmas observance) because all but
        two historical proclamation holidays were on Christmas Eve, leaving
        insufficient information to consider other dates.

        Returns
        -------
        Returns probability the day will be a future proclaimed holiday, False
        otherwise.
        """
        self._set_holidays()
        return (
            0
            if self.ts.year <= 2023
            or (self.ts.month != 12 and self.ts.day not in [22, 23, 24])
            else self._holidays.estimate_future_proclamation_holidays(
                future_dates=self.ts
            )
        )

    @property
    def probable_mil_passday(self) -> bool:
        """
        Estimates if the ts is likely a military pass day.

        Returns
        -------
        True if the ts is likely a military pass day, False otherwise.

        Notes
        -----
        Future versions of this method will add customization options for the
        heuristic used to determine these dates. Military passdays associated
        with holidays are highly variable across commands and locations based
        on a range of factors. However, the majority fall into a reasonably
        predictable pattern. Results from this method should be accurate for
        the majority of cases, and otherwise provide an approximation
        for predictable gaps in military person-power.

        """
        passday = MilitaryPassDay()
        return passday.is_on_offset(dt=self.ts)

    # payday properties
    @property
    def mil_payday(self) -> bool:
        """
        Checks if the date is a military payday based on DFAS pay schedule.

        Returns
        -------
        True if the ts is a military payday, False otherwise.

        """
        milpay = MilitaryPayDay()
        return milpay.is_on_offset(dt=self.ts)

    @property
    def civ_payday(self) -> bool:
        """
        Checks if the date is a civilian payday.

        Returns
        -------
        True if the date is a civilian payday, False otherwise.

        Notes
        -----
        Method is based on the Federal biweekly pay schedule, which applies to
        *nearly* all, but **not all**, Federal employee.

        """
        payday = FedPayDay()
        return payday.is_on_offset(dt=self.ts)

    # FY/FQ properties
    @property
    def fq(self) -> int:
        """
        Retrieves the fiscal quarter of the date.

        Returns
        -------
        An integer representing the fiscal quarter (1-4).
        """
        self._set_fiscalcal()
        return self._fiscalcal.fqs.iat[0]

    @property
    def fy(self) -> int:
        """
        Retrieves the fiscal year of the date.

        Returns
        -------
        An integer representing the fiscal year (e.g. 23 for FY23).

        """
        self._set_fiscalcal()
        return self._fiscalcal.fys.iat[0]

    @property
    def fy_fq(self) -> str:
        """
        Retrieves the fiscal year and quarter of the date.

        Returns
        -------
        A string representing the fiscal year and quarter (e.g. 2023Q1).
        """
        self._set_fiscalcal()
        return self._fiscalcal.fys_fqs.to_series().iat[0]

    @property
    def is_fq_start(self) -> bool:
        """
        Checks if the date is the start of a fiscal quarter.

        Returns
        -------
        True if the date is the start of a fiscal quarter, False otherwise.

        """
        self._set_fiscalcal()
        return self._fiscalcal.fq_start.to_timestamp().to_series().iloc[0] == self.ts

    @property
    def is_fq_end(self) -> bool:
        """
        Checks if the date is the end of a fiscal quarter.

        Returns
        -------
        True if the date is the end of a fiscal quarter, False otherwise.

        """
        self._set_fiscalcal()
        return self._fiscalcal.fq_end.to_timestamp().to_series().iloc[0] == self.ts

    @property
    def is_fy_start(self) -> bool:
        """
        Checks if the date is the start of a fiscal year.

        Returns
        -------
        True if the date is the start of a fiscal year, False otherwise.

        """
        self._set_fiscalcal()
        return self.ts in self._fiscalcal.fy_start

    @property
    def is_fy_end(self) -> bool:
        """
        Checks if the date is the end of a fiscal year.

        Returns
        -------
        True if the date is the end of a fiscal year, False otherwise.

        """
        self._set_fiscalcal()
        return self.ts in self._fiscalcal.fy_end

    # department and appropriations related status properties

    def get_departments_by_status(self, status_key: str):
        """
        Retrieve departments matching a specific status. This is the primary
        getter method for FedStamp's status-related property methods.

        Parameters
        ----------
        status_key
            The key representing the status to filter departments by.

        Returns
        -------
        A dictionary of departments and their status, filtered by the
        specified status key.

        """
        pass

    @property
    def departments(self) -> set[str]:
        """
        Retrieves the set of executive departments active on the date.

        Returns
        -------
        A set of Dept enums.

        """
        pass

    @property
    def all_depts_status(self):
        """
        Retrieves the status of all departments.

        Returns
        -------
        A StatusDictType mapping each department to its status on the date.

        """
        pass

    @property
    def all_depts_full_approps(self) -> bool:
        """
        Checks if all departments were/are fully appropriated on the date.

        Returns
        -------
        True if all departments are fully appropriated, False otherwise.

        """
        pass

    @property
    def all_depts_cr(self) -> bool:
        """
        Checks if all departments are/were under a continuing resolution on
        the date.

        Returns
        -------
        True if all departments are under a continuing resolution, False
        otherwise.
        """
        pass

    @property
    def all_depts_funded(self) -> bool:
        """
        Checks if all departments were/are either fully appropriated or under
        a continuing resolution on the date.

        Returns
        -------
        True if all departments are either fully appropriated or under a
        continuing resolution, False otherwise.
        """
        pass

    @property
    def all_unfunded(self) -> bool:
        """
        Checks if all departments were/are unfunded (appropriations gap or
        shutdown) on the date.

        Returns
        -------
        True if all departments are unfunded, False otherwise.
        """
        pass

    @property
    def gov_cr(self) -> bool:
        """
        Checks if *any* departments were/are under a continuing resolution on
        the date.

        Returns
        -------
        True if the pdtimestamp is during a continuing resolution, False
        otherwise.
        """
        pass

    @property
    def gov_shutdown(self) -> bool:
        """
        Checks if *any* departments were/are shutdown on the date.

        Returns
        -------
        True if the pdtimestamp is during a shutdown, False otherwise.
        """
        pass

    @property
    def gov_approps_gap(self) -> bool:
        """
        Checks if the date was/is during an appropriations gap for *any*
        departments.

        Returns
        -------
        True if the date is during an appropriations gap, False otherwise.
        """
        pass

    @property
    def gov_unfunded(self) -> bool:
        """
        Checks if any departments were/are either subject to a gap in
        appropriations or shutdown on the date.

        Returns
        -------
        True if the date is during a funding gap.

        """
        pass

    @property
    def full_op_depts(self):
        """
        Retrieves departments that were/are fully operational (i.e. had
        full-year appropriations) on the date.

        Returns
        -------
        A StatusDictType dictionary representing departments that are fully
        operational.
        """
        pass

    @property
    def funded_depts(self):
        """
        Retrieves departments that were/are either fully operational or under
        a continuing resolution on the date.

        Returns
        -------
        A StatusDictType dictionary representing departments that are either
        fully operational or under a continuing resolution.
        """

    @property
    def cr_depts(self):
        """
        Retrieves departments that were/are under a continuing resolution on
        the date.

        Returns
        -------
        A StatusDictType dictionary representing departments that are under a
        continuing resolution.
        """
        pass

    @property
    def gapped_depts(self):
        """
        Retrieves departments that were/are under an appropriations gap on the
        date (but not shutdown).

        Returns
        -------
        A StatusDictType dictionary representing departments that are in an
        appropriations gap.

        """
        pass

    @property
    def shutdown_depts(self):
        """
        Retrieves departments that were/are shut down for the date.

        Returns
        -------
        A StatusDictType dictionary representing departments that are shut
        down.

        """
        pass

    @property
    def unfunded_depts(self):
        """
        Retrieves departments that were/are unfunded for the date
        (either under an appropriations gap or fully shutdown).

        Returns
        -------
        A StatusDictType dictionary representing departments that are unfunded.

        """
        pass


def to_fedstamp(*date: FedStampConvertibleTypes) -> FedStamp:
    """
    Converts a date to a FedStamp object.

    Parameters
    ----------
    date : FedStampConvertibleTypes
        The date to convert.

    Returns
    -------
    FedStamp
        The FedStamp object representing the date.

    """
    if count := len(date):
        if count in {1, 3}:
            date = tuple(date) if count == 3 else date
            return FedStamp(ts=to_timestamp(date))
    raise ValueError(
        f"invalid number of arguments: {count}. "
        "to_fedstamp() requires either 1 argument, or 3 integers as YYYY, M, D"
    )
