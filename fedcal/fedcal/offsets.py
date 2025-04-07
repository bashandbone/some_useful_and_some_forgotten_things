# fedcal offsets.py
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
Provides a series of custom pandas offset classes, either for direct use or
integration with FedStamp and FedIndex, namely: federal holidays, business
days, and fiscal years/quarters.

The offsets module includes offsets for:
- Civilian biweekly paydays (`FedPayDay`, customized from `Week`)
- holidays (`FedHolidays`, customized from `AbstractHolidayCalendar`)
- business days (`FedBusinessDay`, customized from `CustomBusinessDay`)
- military paydays (`MilitaryPayDay`, heavily customized from
`SemiMonthOffset`)
- military passdays (`MilitaryPassDay`, a frankensteinly customized from
`CustomBusinessDay`), which provides an offset for identifying probable
passdays falling on businessdays adjacent to Federal holidays. It allows some
customization of the rules used to identify passdays.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import timedelta
from typing import ClassVar, Literal

import numpy as np
import pandas as pd
from numpy import datetime64, int32, int64, timedelta64
from numpy.typing import NDArray
from pandas import DatetimeIndex, Index, Series, Timedelta, Timestamp
from pandas._libs.tslibs.offsets import SemiMonthOffset, apply_wraps, shift_month
from pandas.tseries.holiday import (
    AbstractHolidayCalendar,
    Holiday,
    USColumbusDay,
    USLaborDay,
    USMartinLutherKingJr,
    USMemorialDay,
    USPresidentsDay,
    USThanksgivingDay,
    nearest_workday,
)
from pandas.tseries.offsets import CustomBusinessDay, Week

from fedcal._typing import DatetimeScalarOrArray, TimestampSeries
from fedcal.enum import DoW
from fedcal.utils import (
    dt64_to_date,
    dt64_to_dow,
    ensure_datetimeindex,
    get_today,
    to_dt64,
)


@dataclass(slots=False, order=False)
class FedPayDay(Week):
    """
    A custom pandas offset class that calculates federal civilian biweekly
    paydays, which occur every other Friday since 2 Jan 1970 (from an epoch
    perspective... people got paid before that too). We adjust and offset
    pandas' Week offset to instead produce a biweekly pattern set to our
    group of Fridays.

    Attributes
    ----------

    normalize : defaulting to True, represents whether to normalize the time
        output to midnight. As we're concerned with days here, we default to
        true to remove the time component.

    Methods
    -------
    is_on_offset(dt: Timestamp) -> bool
        Checks if a given date or array of dates is on a federal civilian
        biweekly payday.

    See Also
    --------
    *Private Methods*:
    _weeks_since_epoch : calculates the number of weeks since the reference
        date (2 Jan 1970)

    _calculate_adjustment : calculates the adjustment to be applied to the
        Week offset to match the correct biweekly pattern.

    _apply : applies the biweekly pattern set by this class to a given
        datetime.

    _apply_array : applies the biweekly pattern set by this class to a
        given array of datetime-like objects."""

    _prefix: str = "FW"

    # changing this will break functionality, represents biweekly pattern
    _n: int = field(default=1)

    _normalize: bool = field(default=True)

    # changing this will break functionality, represents Fridays
    _weekday: int = field(default=4)

    def __post_init__(self) -> None:
        """
        Initializes the parent Week() class.
        """

        super().__init__(
            n=self._n,
            normalize=self._normalize,
            weekday=self._weekday,
        )

    def is_on_offset(self, dt: DatetimeScalarOrArray) -> bool | NDArray[bool]:
        """
        Check if a given datetime-like object or array of datetime-like
        objects falls on the offset.

        Parameters
        ----------
        dt : datetime-like object to check

        Returns
        -------
        bool or array of bool, depending on whether `dt` is a scalar or an
        array of datetime-like objects.
        """
        day_mask = dt64_to_dow(dt)[1] == self._weekday
        weeks_since_ref: int | NDArray[int] = self._weeks_since_epoch(dt=dt)
        return dt[((weeks_since_ref % 2) == 0) & day_mask]

    def _weeks_since_epoch(self, dt: DatetimeScalarOrArray) -> int | NDArray[int]:
        """
        Calculates weeks since the epoch for internal offset calculations.
        We take advantage of the fact that the first payday was the second
        day of the epoch to simplify calculations.

        Parameters
        ----------
        dt
            any datetime-like object or array of datetime-like objects.

        Returns
        -------
            int or array of int representing the number of weeks since the
            epoch, depending on input.
        """
        days = (
            dt.value if pd.api.types.is_scalar(val=dt) else dt.astype("int64")
        ) // 86_400_000_000_000

        # The first payday was the 2nd day of the epoch (2 Jan 1970)
        # so we just subtract a day
        return (days - 1) // 7

    def _calculate_adjustment(
        self, dt: pd.Timestamp | NDArray[datetime64] | DatetimeIndex
    ) -> int | NDArray[timedelta64]:
        """
        Calculates the offset adjustment to align the offset with the correct
        biweekly period.

        Parameters
        ----------
        dt
            datetime-like object or array of datetime-like objects.

        Returns
        -------
            binary int or array of int representing the adjustment.
        """
        weeks_since_ref = self._weeks_since_epoch(dt=dt)
        if pd.api.types.is_scalar(val=dt):
            return np.where(weeks_since_ref % 2 == 1, 1, 0)
        return np.where(
            weeks_since_ref % 2 == 1, np.timedelta64(7, "D"), np.timedelta64(0, "D")
        )

    @apply_wraps
    def _apply(self, other) -> Timestamp:
        """
        Applies our custom biweekly alignment before using Week's internal
        _apply method for applying offsets to scalars.

        Parameters
        ----------
        other
            scalar datetime-like object

        Returns
        -------
            Timestamp object with the offset applied.
        """
        adjustment: int | NDArray[int] | None = self._calculate_adjustment(dt=other)
        return super()._apply(other) + Week(n=adjustment * self._n)

    def _apply_array(self, dtarr: NDArray[datetime64]) -> NDArray[datetime64]:
        """
        Applies our custom biweekly alignment after using Week's internal
        _apply_array method for applying the offset to an array.

        Parameters
        ----------
        dtarr
            array of datetime objects

        Returns
        -------
            NDArray of datetime64 objects with the offset applied.
        """
        dtarr = to_dt64(dt=dtarr)
        initial_offset = super()._apply_array(dtarr)
        adjustments: NDArray[timedelta64] = self._calculate_adjustment(
            dt=initial_offset.copy()
        )

        return initial_offset.astype("datetime64[ns]") + adjustments


# Custom Holiday objects; it bothers me that only half of the rules in
# USFederalHolidayCalendar have their own variable. I know it's because of
# their offsets, but... I just had to.

NewYearsDay = Holiday(name="New Year's Day", month=1, day=1, observance=nearest_workday)
MartinLutherKingJr: Holiday = USMartinLutherKingJr
PresidentsDay: Holiday = USPresidentsDay
MemorialDay: Holiday = USMemorialDay
Juneteenth = Holiday(
    name="Juneteenth National Independence Day",
    month=6,
    day=19,
    start_date=pd.Timestamp(year=2021, month=6, day=18),
    observance=nearest_workday,
)
IndependenceDay = Holiday(
    name="Independence Day", month=7, day=4, observance=nearest_workday
)
LaborDay: Holiday = USLaborDay
ColumbusDay: Holiday = USColumbusDay
VeteransDay = Holiday(name="Veterans Day", month=11, day=11, observance=nearest_workday)
ThanksgivingDay: Holiday = USThanksgivingDay
ChristmasDay = Holiday(
    name="Christmas Day", month=12, day=25, observance=nearest_workday
)


@dataclass(order=False, slots=False)
class FedHolidays(AbstractHolidayCalendar):

    """
    Custom implementation based on pandas' USFederalHolidayCalendar and using
    pandas' AbstractHolidayCalendar base/meta calendar.

    Customized to add additional functionality and supply proclaimed holidays.

    US Federal Government Holiday Calendar based on rules specified by:
    https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/

    Attributes
    ----------
    rules : a list of pd.Holiday objects representing all federal holidays,
        including proclamation holidays.
    proclaimed_holidays : Separate collection of holidays proclaimed by
        executive orders.
    scheduled_holidays : Separate collection of scheduled holidays (omits
    proclaimed_holidays)

    np_holidays : vectorized holidays in a numpy array for faster operations

    Methods
    -------

    """

    _prefix: str = "FH"

    name: ClassVar[str] = "USFederalHolidays"

    rules: ClassVar[list[Holiday]] = [
        NewYearsDay,
        MartinLutherKingJr,
        PresidentsDay,
        MemorialDay,
        Juneteenth,
        IndependenceDay,
        LaborDay,
        ColumbusDay,
        VeteransDay,
        ThanksgivingDay,
        ChristmasDay,
        # now for proclamation holidays:
        Holiday(
            name="2020 Christmas Eve proclamation (Trump)", year=2020, month=12, day=24
        ),
        Holiday(
            name="2019 Christmas Eve proclamation (Trump)", year=2019, month=12, day=24
        ),
        Holiday(
            name="2018 Christmas Eve by proclamation (Trump)",
            year=2018,
            month=12,
            day=24,
        ),
        Holiday(
            name="2015 Christmas Eve proclamation (Obama)", year=2015, month=12, day=24
        ),
        Holiday(
            name="2014 Christmas Eve proclamation (Obama)", year=2014, month=12, day=26
        ),
        Holiday(
            name="2012 Christmas Eve proclamation (Obama)", year=2012, month=12, day=24
        ),
        Holiday(
            name="2007 Christmas Eve proclamation (GW Bush)",
            year=2007,
            month=12,
            day=24,
        ),
        Holiday(
            name="2001 Christmas Eve proclamation (GW Bush)",
            year=2001,
            month=12,
            day=24,
        ),
        Holiday(
            name="1979 Christmas Eve proclamation (Carter)", year=1979, month=12, day=24
        ),
        Holiday(
            name="1973 New Year's Eve proclamation (Nixon)", year=1973, month=12, day=31
        ),
        Holiday(
            name="1973 Christmas Eve proclamation (Nixon)", year=1973, month=12, day=24
        ),
    ]

    proclaimed_holidays: ClassVar[list[Holiday]] = [rule for rule in rules if rule.year]
    scheduled_holidays: ClassVar[list[Holiday]] = [
        rule for rule in rules if not rule.year
    ]

    np_holidays: NDArray[datetime64] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """
        Make sure Abstract Holiday calendar and our attributes are running
        properly.
        """
        super().__init__(name=type(self).name, rules=type(self).rules)
        if not self.np_holidays:
            self.np_holidays = to_dt64(dt=self.holidays(), freq="D")

    def holidays(
        self,
        start: Timestamp = None,
        end: Timestamp = None,
        return_name: bool = False,
        with_proclamation: bool = True,
    ) -> DatetimeIndex | Series[str]:
        """
        Implements parent classes's method of the same name. Returns
        DatetimeIndex of holidays for either given dates or class dates
        (1970-2199). Optional return flag returns a series with holidays
        named.

        Parameters
        ----------
        start : start date for the range, defaults to class dates if None.
        end : end date for the range, defaults to class dates if None.
        return_name : whether to return a series with holidays named.
        Defaults to False.
        with_proclamation : whether to include historical proclamation
        holidays (i.e. one-off Christmas Eves), defaults to True.

        Returns
        -------
        DatetimeIndex of holidays between the start and end dates, or
        Series of holidays with names of holidays if return_name flag
        and dates as the index.
        """
        if with_proclamation:
            return super().holidays(start=start, end=end, return_name=return_name)
        else:
            return AbstractHolidayCalendar(
                rules=type(self).scheduled_holidays
            ).holidays(start=start, end=end, return_name=return_name)

    def proclamation_holidays(
        self,
        start: Timestamp | None = None,
        end: Timestamp = None,
        return_name: bool = False,
    ) -> DatetimeIndex | TimestampSeries:
        """
        Retrieve dates for proclamation holidays only. If dates provided,
        returns only within date range. If return_name flag given, returns a
        series with holidays named, otherwise a DatetimeIndex with only dates.

        Parameters
        ----------
        start : start date for the range, defaults to class dates if None.
        end : end date for the range, defaults to class dates if None.
        return_name : whether to return a series with holidays named.
        Defaults to False.

        Returns
        -------
        DatetimeIndex of holidays between the start and end dates, or
        Series of holidays with names of holidays if return_name flag
        and dates as the index.
        """
        only_proc_hols_instance: AbstractHolidayCalendar = AbstractHolidayCalendar(
            name="USFederalProclamationHolidays", rules=type(self).proclaimed_holidays
        )
        return only_proc_hols_instance.holidays()

    def _calculate_historical_probabilities(self) -> Series[float]:
        """
        Handles the heavier work of calculating the probabilities
        for estimate_future_proclamation_holidays.

        Returns
        -------
            series of floats giving rough probabilities a future
            Christmas Eve may be a proclamation holiday based on
            its day of the week compared to historical trends.
        """
        _hist_xmas: DatetimeIndex = ChristmasDay.dates(
            start_date="1970-01-01", end_date=get_today().tz_localize(None)
        )
        _hist_xmas_dow_counts: Series[
            int
        ] = _hist_xmas.to_series().dt.dayofweek.value_counts()
        _hist_p_hols: Series[Timestamp] = self.proclamation_holidays().to_series()

        _hist_p_hols_years: Series[int] = _hist_p_hols.dt.year
        _matched_xmas: DatetimeIndex = _hist_xmas[
            _hist_xmas.year.isin(_hist_p_hols_years)
        ]
        _matched_xmas_dow_counts: Series[
            int
        ] = _matched_xmas.to_series().dt.dayofweek.value_counts()
        return (_matched_xmas_dow_counts / _hist_xmas_dow_counts).fillna(value=0)

    def estimate_future_proclamation_holidays(
        self,
        future_dates: Timestamp | TimestampSeries | DatetimeIndex,
    ) -> Series[float]:
        """
        Roughly estimate if a future Christmas Eve may be proclaimed a holiday
        based on Christmas Day's weekday. Of the 10 such proclamations to
        date, 6 (60%) fell on a Tuesday, 2 on a Friday, and 1 each on
        Wednesday and Thursday. The associated proclamation holiday for the
        Thursday actually fell on the 26th... we omit the 26th here because 1
        is not a pattern... The same goes for Nixon's surprise New Year's Eve.

        Parameters
        ----------
        future_dates : Dates for which to guess the holidays.

        Returns
        -------
        A Series of dates with float probabilities they could be declared a
        proclamation holiday based on their day of week and whether they're a
        Christmas Eve.

        """
        dates = ensure_datetimeindex(dt=future_dates)
        max_past: Timestamp = get_today()
        if dates.tzinfo or max_past.tzinfo:
            dates = dates.tz_localize(None) if dates.tzinfo else dates
            max_past = max_past.tz_localize(None) if max_past.tzinfo else max_past
            if dates.max() <= max_past:
                raise ValueError(
                    "No dates in provided index are in the future, latest"
                    f"date was: {dates.max()}"
                )

        historical_probabilities: Series[
            float
        ] = self._calculate_historical_probabilities()
        eval_dates: DatetimeIndex = dates[
            (dates.month == 12)
            & (dates.day == 24)
            & (dates.dayofweek < 5)
            & (dates > max_past)
        ]

        if eval_dates.empty:
            return pd.Series(data=np.zeros(shape=len(dates), dtype=bool), index=dates)

        probabilities = pd.Series(
            data=np.zeros(shape=len(dates), dtype=float), index=dates
        )
        eval_probabilities = eval_dates.dayofweek.map(
            mapper=historical_probabilities
        ).fillna(value=0)
        probabilities[eval_dates] = eval_probabilities
        return probabilities


@dataclass(order=False, slots=False)
class FedBusinessDay(CustomBusinessDay):

    """
    Class representing federal business days, adjusted for federal holidays.
    As a CustomBusinessDay object, it may be directly applied to a pandas
    timeseries with simple addition/subtraction (see examples below):

    Attributes
    ----------
    self : CustomBusinessDay child class (the most important thing here)
    You probably won't need to touch any of these defaults and can happily
    call it as FedHolidays()

    _weekmask : defaults to "Mon Tue Wed Thu Fri", and business day in most
    situations, but here if you need to pass a custom weekmask. Can be pass as
    either binary representing each day of the week starting with Monday (e.g.
    '1111100' is Mon-Fri), or three-letter strings of just the business days.

    _normalize : True -- normalized offset. Note, it will not pass equality
        tests with non-normalized offsets.

    _holidays : default is derived from FedHolidays, providing federal holidays

    _calendar : We default to a numpy busdaycalendar with vectorized holidays.

    off_set : alias for offset, for shifting more than one day pass a
    timedelta object. Default is 0.

    Methods
    -------
    *inherits methods from CustomBusinessDay and BusinessDay, such as:

    is_on_offset(dt: Timestamp) -> bool
        Checks if a given date is on a federal business day.

    rollback(dt: Timestamp) -> Timestamp
        rolls the date back to the previous business day if not a business day

    rollforward(dt: Timestamp) -> Timestamp
        rolls the date forward to the next business day if not a business day

    Examples
    --------
    ```python
    # Create a DatetimeIndex of only business days:
    >>> import pandas as pd
    >>> import fedcal as fc
    >>> fbd = fc.FedBusinessDay()
    >>> bdays = pd.date_range(start="2021-01-01", end="2022-01-10", freq=fbd)

    # Shift the result to the next business day (next day on the offset) --
    # for Timestamp or across a DatetimeIndex/Timestamp Series
    >>> ts = pd.to_datetime('2024-1-1') # New Years' Day, a Monday
    >>> fbd.is_on_offset(ts)
    False
    >>> next_business_day = ts + fbd   # subtract for the prior business day
    2024-1-2 00:00:00

    # Add 5 business days for processing (or subtract, or whatever):
    >>> five_bdays = your_datetimeindex + fc.FedBusinessDay(offset=pd.Timedelta
    (days=5))
    ```
    """

    _prefix: str = "F"

    _weekmask: list[str] = field(default="1111100")
    _normalize: bool = field(default=True, init=False)

    _holidays: list[Timestamp] | NDArray[np.datetime64] | None = field(
        default=FedHolidays().np_holidays
    )
    off_set: timedelta | Timedelta = field(default=timedelta(days=0), init=False)

    def __post_init__(self) -> None:
        """We make sure CBD initiates properly."""
        cal = np.busdaycalendar(weekmask=self._weekmask, holidays=self._holidays)
        super().__init__(
            n=1,
            normalize=self._normalize,
            calendar=cal,
            offset=self.off_set,
        )

    def is_on_offset(self, dt: DatetimeScalarOrArray) -> bool | NDArray[bool]:
        """
        Checks if a given date is on a federal business day.

        Parameters
        ----------
        dt : either a single pd.Timestamp, a Series of
        Timestamps, or DatetimeIndex for offsetting with fed_business_days.

        Returns
        -------
        A boolean scalar or array reflecting business days in the range.
        """
        dt = to_dt64(dt=dt)
        scalar: bool = pd.api.types.is_scalar(val=dt)
        b_day = np.is_busday(dates=dt, busdaycal=self.calendar)
        return b_day[0] if scalar and isinstance(b_day, np.ndarray) else b_day

    def _roll(
        self, dt: DatetimeScalarOrArray, roll: Literal["forward", "backward"]
    ) -> datetime64 | NDArray[datetime64]:
        dt = to_dt64(dt=dt)
        if pd.api.types.is_scalar(val=dt):
            return (
                dt
                if self.is_on_offset(dt=dt)
                else np.busday_offset(
                    dates=dt, offsets=0, roll=roll, busdaycal=self.calendar
                )
            )
        mask = ~(self.is_on_offset(dt=dt))
        dt[mask] = np.busday_offset(
            dates=dt[mask], offsets=0, roll=roll, busdaycal=self.calendar
        )
        return dt

    def rollback(self, dt: DatetimeScalarOrArray) -> datetime64 | NDArray[datetime64]:
        """
        Rolls a date back to the last prior business day, if it isn't a
        business day.

        Parameters
        ----------
        dt
            datetime scalar or array to rollback

        Returns
        -------
            either the date(s) if it is on a business day or the prior business day(s).
        """
        return self._roll(dt=dt, roll="backward")

    def rollforward(
        self, dt: DatetimeScalarOrArray
    ) -> datetime64 | NDArray[datetime64]:
        """
        Rolls a date(s) forward to the next business day if it isn't a business
        day.

        Parameters
        ----------
        dt
            datetime scalar or array to roll forward

        Returns
        -------
            Date(s) either rolled forward to next business day or returned if
            on a business day.
        """
        return self._roll(dt=dt, roll="forward")

    def get_business_days(
        self, dates: Timestamp | TimestampSeries | DatetimeIndex, as_bool: bool = False
    ) -> DatetimeIndex | Series[bool] | None:
        """
        Retrieve a Datetimeindex of business days. If as_bool flag is True,
        returns a boolean array of the same length as the input dates.

        Parameters
        ----------
        dates : either a single pd.Timestamp, a Series of
        Timestamps, or DatetimeIndex for offsetting with fed_business_days.
        as_bool : whether to return a boolean array. Defaults to False.

        Returns
        -------
        DatetimeIndex of business days. If as_bool flag is True, returns a
        boolean array reflecting business days in the range.

        """
        dates = ensure_datetimeindex(dt=dates)
        with warnings.catch_warnings():
            warnings.simplefilter(action="ignore")
            if as_bool:
                return dates.isin(values=(dates + self))
            else:
                dates + self


@dataclass(slots=False, order=False)
class MilitaryPayDay(SemiMonthOffset):
    """
    Custom date offset class based on pandas' SemiMonthOffset for efficient
    date calculations of military paydays based on their rules of falling on
    the 1st or 15th of the month if they are business days, else soonest prior
    business day. We use FedBusinessDay's underlying numpy calendar for
    efficient vector operations on the date shifts.

    Attributes
    ----------

    _normalize: default is true, as this is a calendar we're mostly concerned
        with dates -- normalizes time values to midnight.

    b_day: FedBusinessDay object used for adjusting business day offsets.
    """

    _min_day_of_month: int = 7

    _normalize: bool = field(default=True, init=False)
    b_day: FedBusinessDay = FedBusinessDay()
    calendar: np.busdaycalendar = field(default=b_day.calendar, init=False)

    def __post_init__(self) -> None:
        """
        Initializes FedHolidays if not yet initialized; initializes
        SemiMonthOffset parent class.
        """
        if not hasattr(self, "calendar"):
            FedHolidays()
            self.b_day = FedBusinessDay()
            self.calendar = self.b_day.calendar
        super().__init__(
            n=1,
            normalize=self._normalize,
            day_of_month=15,
        )

    def is_on_offset(self, dt: DatetimeScalarOrArray) -> bool | NDArray[bool]:
        """
        Check if the date(s) is on the offset.

        Parameters
        ----------
        dt : datetime scalar or array to check for being useful.

        Returns
        -------
        bool or array of bool for values on offset.

        """
        if pd.api.types.is_scalar(val=dt):
            return self._check_scalar_on_offset(dt=dt)
        return self._check_array_on_offset(dtarr=dt)

    def _check_scalar_on_offset(self, dt: Timestamp) -> bool:
        """
        Checks scalar if it is on the offset

        Parameters
        ----------
        dt
            datetime scalar for checking

        Returns
        -------
            True if the date is on the offset.
        """
        if self.b_day.is_on_offset(dt=dt) and dt.day in [1, 15]:
            return True
        if self.b_day.is_on_offset(dt=dt) and (15 - 3 < dt.day < 15):
            return self.b_day.rollback(date=dt)(dt=dt.replace(day=15)) == dt
        if self.b_day.is_on_offset(dt=dt) and dt.day > 24:
            next_month = dt + pd.Timedelta(months=1)
            return self.b_day.rollback(date=dt)(dt=next_month.replace(day=1)) == dt
        return False

    def _check_array_on_offset(
        self, dtarr: NDArray[datetime64] | DatetimeIndex | TimestampSeries
    ) -> NDArray[bool]:
        """
        Checks an array for values on the offset.

        Parameters
        ----------
        dtarr
            array of datetimes to check

        Returns
        -------
            An NDArray of bool value reflecting days of the week.
        """
        dti: DatetimeIndex = pd.DatetimeIndex(data=dtarr.copy())

        offset: NDArray[datetime64] = self.b_day.rollback(
            dt=dti[dti.day.isin(values=[1, 15])]
        )
        return dti.isin(values=offset)

    @apply_wraps
    def _apply(self, other: Timestamp) -> Timestamp:
        """
        Overrides parent's _apply method. Responsible for applying an offset
        to a datetime scalar.

        Parameters
        ----------
        other
            datetime scalar to be offset

        Returns
        -------
            Date adjusted by the offset.
        """
        if self.n > 0:
            target_day: int = 15 if other.day < 15 else 1
            other = shift_month(other, self.n) if other.day >= 15 else other
        else:
            target_day = 15 if other.day > 15 else 1

        adjusted_date = other.replace(day=target_day)
        return self.b_day.rollback(adjusted_date)

    def _apply_array(self, dtarr: NDArray[datetime64]) -> NDArray[datetime64]:
        """
        Applies the offset to an array input.

        Parameters
        ----------
        dtarr
            A datetime array for offsetting

        Returns
        -------
            Offset array.
        """
        np_dtstruct: NDArray[datetime64, int32] = dt64_to_date(dtarr=dtarr.copy())
        days = np_dtstruct[..., 3]

        is_target: NDArray[bool] = np.isin(element=days, test_elements=[1, 15])
        busdays = np.is_busday(np_dtstruct[..., 0][is_target], busdaycal=self.calendar)
        non_busdays_idx = np.where(is_target & ~busdays)[0]

        offset_dates: NDArray[datetime64] = self.b_day.rollback(
            dt=np_dtstruct[..., 0][is_target]
        )

        off_arr: NDArray[datetime64] = dtarr.copy().astype(dtype="datetime64[D]")
        off_arr[non_busdays_idx] = offset_dates

        return off_arr

    def rollback(self, dt: DatetimeScalarOrArray):
        raise NotImplementedError("rollback not yet implemented")

    def rollforward(self, dt: DatetimeScalarOrArray):
        raise NotImplementedError("rollforward not yet implemented")

    # TODO: implement custom rollback/rollforward with array support


@dataclass(order=False, slots=False)
class MilitaryPassDay(CustomBusinessDay):
    """
    A custom pandas DateOffset class for *probable* military passdays
    business-day-adjacent to federal holidays. With passdays reflected as only
    the affected normal business day vice the entire period if it spans a
    weekend.

    Because passday practices can be very localized, we set a default mapping
    of probable passdays based on holiday day of the week in self.passday_map,
    with default behavior as follows: Mon & Thu holidays have corresponding
    Friday passdays, Friday and Tuesday holidays mapped to Monday passdays, and
    Wednesday to Thursday. You can change these values by passing your own
    dictionary to self.passday_map using three-letter strings for each day in
    title case, e.g. {"Mon": "Fri", "Tue": "Mon", "Wed": "Thu"}. The mapping
    for each value must be to an adjacent business day, and weekends cannot be
    mapped to either value. Perhaps a future version can implement more
    flexibility, please fork and open a pull request.

    In case you're wondering why MilitaryPassDay is a child of
    CustomBusinessDay, there really isn't a good reason. We needed the core
    DateOffset logic and helper methods from any of the day-based child
    classes to DateOffset. For consistency we still use FedBusinessDay for
    business day related calculations.

    Methods
    -------
    is_on_offset : returns True if the date is on the offset, False otherwise.

    nearest_holiday : a handy utility that can find the nearest holiday to any
    date-like object, whether scalar or array. Used in passday calculations,
    but available for broader use because it's spiffy.

    Attributes
    ----------

    offset: defaults to timedelta(days=0). Not fully implemented and unlikely
    to be useful for most users, but on the to-do list for eventual
    implementation.

    b_day: FedBusinessDay object used for adjusting business day offsets.

    passday_map: default mappings of holiday day-of-week to
    passday-day-of-week. You may provide custom mappings meeting criteria in
    the _passday_reqs property

    Raises
    ------
    ValueError
        If the passday map is not a valid mapping of holiday-day-of-the-week
        to passday-day-of-the-week. Message describing criteria is both the
        error message and a property, _passday_reqs.
    NotImplementedError
        If the n, weekmask, or offset attributes are changed.


    Notes
    -----
    *Private Methods*:
        __post_init__ : initializes the parent CustomBusinessDay class
            and sets the internal mapping of holiday-day-of-week to passdays
        _set_map : sets the internal mapping of holiday-day-of-week to passdays
        _passday_reqs : describes the requirements for a valid passday map.
        _validate_map : validates the internal mapping of holiday-day-of-week
            to passdays
        _apply : Custom implementation of the parent CustomBusinessDay class's
            _apply method, which handles scalar date offsets.
        _apply_array : Custom implementation of the parent CustomBusinessDay's
            _apply_array method, which handles array date offsets.
    """

    _prefix: str = "CDP"

    _normalize: bool = field(default=True, init=False)

    b_day = FedBusinessDay()

    # mapping of holiday-day-of-the-week to passday-day-of-the-week
    # default is Friday passday for Thursday or Monday holiday, Monday passday
    # for Friday or Tuesday holiday, and Thursday passday for Wednesday holiday
    passday_map: dict[str, str] = field(
        default={
            "Mon": "Fri",  # [key] holiday day of observance to:
            "Tue": "Mon",  # value day of associated passday
            "Wed": "Thu",
            "Thu": "Fri",
            "Fri": "Mon",
        }
    )

    _map: dict | None = None

    def _post_init__(self) -> None:
        """
        Validates attributes and initializes the parent class.

        Raises
        ------
        NotImplementedError
            If core attributes n, weekmask,or offset are not their default
            values.
        """
        if not hasattr(self.b_day, "calendar"):
            FedHolidays()
            self.b_day = FedBusinessDay()
        super().__init__(
            n=1,
            normalize=self._normalize,
            calendar=self.b_day.calendar,
        )
        self._map = self._set_map()
        self._validate_map()

    def _set_map(self) -> dict[DoW, DoW]:
        """
        Sets the internal mapping for holidays to passdays.
        """
        return {
            DoW.__members__.get(k.upper()): DoW.__members__.get(v.upper())
            for k, v in self.passday_map.items()
        }

    @property
    def _passday_reqs(self) -> str:
        """
        Provides requirements for passday_map to pass validation, used as an
        error message.
        """
        return """Passday map must:
                1) Use 5 unique weekday keys and 5 unique
                values (each consisting of weekdays).
                2) Keys and values must have valid string representations of
                DoW objects (three letter weekdays (e.g. Tue))
                3) Keys and values must be within one adjacent businessday
                4) Keys and values cannot be the same.
                5) Keys or values cannot be Saturday or Sunday.
                """

    def _validate_map(self) -> None:
        """
        Validates the passday_map

        Raises
        ------
        ValueError
            If criteria in _passday_reqs are not met.
        """
        if (
            len(self._map.keys()) != 5
            or len(self._map.values()) != 5
            or not all(isinstance(v, DoW) for v in self._map.values())
            or any(v > 4 for v in self._map.values())
        ):
            raise ValueError(
                f"map failed key-value composition checks {self._passday_reqs}"
            )
        for k, v in self._map.items():
            if (
                k == v
                or (k in [4, 0] and abs(k - v) not in [1, 4])
                or (k in [1, 2, 3] and abs(k - v) != 1)
            ):
                raise ValueError(
                    "map failed proximity checks -- days must be within one"
                    f"business day of each other. {self._passday_reqs}"
                )

    def _check_scalar_on_offset(self, dt: Timestamp) -> bool:
        """
        Checks if a scalar date is on the offset.

        Parameters
        ----------
        dt
            Timestamp date to check

        Returns
        -------
            True if date on offset
        """
        if not self.b_day.is_on_offset(dt):
            return False
        dt = pd.Timestamp(dt)
        dt_dow = dt.dayofweek
        hol = pd.Timestamp(self.nearest_holiday(other=dt))
        diff = abs((dt - hol).days)
        if diff not in {1, 3}:
            return False
        if diff == 3 and dt_dow not in {0, 4}:
            return False
        return self._map[DoW(value=hol.dayofweek)] == DoW(value=dt_dow)

    def _check_array_on_offset(self, dtarr: NDArray[datetime64]) -> NDArray[bool]:
        """
        Checks if an array of dates is on the offset.

        Parameters
        ----------
        dtarr
            Array of dates to check

        Returns
        -------
            Array of booleans, True if date on offset
        """
        dtarr: DatetimeIndex = pd.to_datetime(arg=dtarr)
        dtarr_dow: Index[int] = dtarr.dayofweek
        hols: DatetimeIndex = pd.to_datetime(self.nearest_holiday(other=dtarr))
        diffs: Index[int] = abs((dtarr - hols).days)
        _map_map: NDArray[int] = np.array(
            object=[self._map[DoW(value=i)].value for i in range(5)]
        )
        cond1 = (diffs == 3) & ((hols.dayofweek == 0) | (hols.dayofweek == 4))
        cond2 = (diffs == 1) & (dtarr_dow < 5)
        cond3 = self.b_day.is_on_offset(dt=dtarr)
        cond4 = _map_map[hols.dayofweek.values] == dtarr_dow.values

        conditions = (cond1 | cond2) & cond3 & cond4

        return np.where(conditions, True, False)

    def is_on_offset(self, dt: DatetimeScalarOrArray) -> bool:
        """
        Tests if a scalar date is on the offset.

        Returns
        -------
        bool
            True if the date is on the offset, False otherwise.
        """
        if pd.api.types.is_scalar(val=dt):
            return self._check_scalar_on_offset(dt=dt)
        return self._check_array_on_offset(dtarr=dt)

    @apply_wraps
    def _apply(self, other: Timestamp) -> Timestamp:
        """
        Custom implementation of the parent CustomBusinessDay class's _apply
        method; applies date offset to a scalar date.

        Parameters
        ----------
        other : Timestamp
            Scalar date to apply offset to.

        Returns
        -------
        Timestamp
            Date with offset applied.

        """
        hol: Timestamp = self.nearest_holiday(other=other)
        hol_dow: int = pd.to_datetime(arg=hol).dayofweek
        pass_dow: DoW = self._map[hol_dow]
        if ((pass_dow < hol_dow) or (hol_dow == 0 and pass_dow == 4)) and (
            hol_dow != 4 and pass_dow != 0
        ):
            return self.b_day.rollback(dt=hol)
        else:
            return self.b_day.rollforward(dt=hol)

    def _apply_array(self, dtarr: NDArray[datetime64]) -> NDArray[datetime64] | None:
        """
        Custom implementation of the parent CustomBusinessDay class's
        _apply_array method; applies date offset to an array of dates.

        Parameters
        ----------
        dtarr : NDArray[datetime64]
            Array of dates to apply offset to.

        Returns
        -------
        NDArray[datetime64]
            Array of dates with offset applied.
        """
        dtarr = to_dt64(dt=dtarr)
        hols: NDArray[datetime64] = self.nearest_holiday(other=dtarr.copy())
        hols_dow: NDArray[int64] = (
            hols.astype("datetime64[D]").view("int64") - 4
        ) % 7  # Day of week for holidays
        pass_dow = np.array(object=[self._map[DoW(value=dow)] for dow in hols_dow])
        roll_backward = (
            (pass_dow < hols_dow) | ((pass_dow == 4) & (hols_dow == 0))
        ) & ~((hols_dow == 4) & (pass_dow == 0))

        offset_dates: NDArray[datetime64] = hols.copy()
        offset_dates[roll_backward] = np.busday_offset(
            dates=hols[roll_backward],
            offsets=0,
            roll="backward",
            busdaycal=self.b_day.calendar,
        )
        offset_dates[~roll_backward] = np.busday_offset(
            dates=hols[~roll_backward],
            offsets=0,
            roll="forward",
            busdaycal=self.b_day.calendar,
        )

        return offset_dates.astype(dtype="datetime64[ns]")

    def nearest_holiday(
        self,
        other: DatetimeScalarOrArray,
        holidays: DatetimeScalarOrArray | None = None,
    ) -> DatetimeScalarOrArray:
        """
        Finds nearest holiday to date or dates, supports vectorized and scalar
        input as long as they implement comparison, subtraction, and abs.

        Adapted from Tamas Hegedus on StackOverflow:
        https://stackoverflow.com/questions/32237862/find-the-closest-date-to-a-given-date

        Parameters
        ----------
        other : date or dates to find nearest holiday to.
        holidays : list of dates to find nearest holiday to.

        Returns
        -------
        nearest holiday(s) to date or dates.

        """
        holidays = self.b_day.calendar.holidays
        if pd.api.types.is_scalar(val=other):
            return min(holidays, key=lambda x: abs((x - other)))
        other: NDArray[datetime64] = (
            other if isinstance(other, np.ndarray) else other.to_numpy()
        )
        diffs = np.abs(other[:, np.newaxis] - holidays)
        return holidays[np.argmin(a=diffs, axis=1)]

    def rollback(self, dt: DatetimeScalarOrArray):
        raise NotImplementedError("rollback not yet implemented")

    def rollforward(self, dt: DatetimeScalarOrArray):
        raise NotImplementedError("rollforward not yet implemented")


__all__: list[str] = [
    "FedPayDay",
    "FedBusinessDay",
    "FedHolidays",
    "MilitaryPayDay",
    "MilitaryPassDay",
]
