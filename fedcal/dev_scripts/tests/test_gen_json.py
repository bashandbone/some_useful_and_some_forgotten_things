# TODO: THIS IS A ROUGH FRAMEWORK FOR TESTING -- IT HASN'T BEEN IMPLEMENTED/FINISHED YET

import gen_json
import pandas
import typing
import unittest
from datetime import timedelta, timezone
from gen_json import Timestamp
from hypothesis import given, strategies as st
from pandas import Interval

# TODO: replace st.nothing() with appropriate strategies


class TestFuzzTimestamp(unittest.TestCase):
    @given(
        ts_input=st.one_of(st.text(), st.integers(), st.floats()),
        year=st.none(),
        month=st.none(),
        day=st.none(),
        hour=st.none(),
        minute=st.none(),
        second=st.none(),
        microsecond=st.none(),
        tzinfo=st.one_of(
            st.none(),
            st.builds(
                timezone,
                offset=st.builds(
                    timedelta,
                    hours=st.integers(min_value=-23, max_value=23),
                    minutes=st.integers(min_value=0, max_value=59),
                ),
            ),
            st.builds(
                timezone,
                name=st.text(alphabet=st.characters()),
                offset=st.builds(
                    timedelta,
                    hours=st.integers(min_value=-23, max_value=23),
                    minutes=st.integers(min_value=0, max_value=59),
                ),
            ),
            st.timezones(),
        ),
        nanosecond=st.one_of(st.sampled_from([None, 0]), st.integers()),
        tz=st.nothing(),
        unit=st.one_of(st.none(), st.text()),
        fold=st.sampled_from([0, None]),
    )
    def test_fuzz_Timestamp(
        self,
        ts_input,
        year,
        month,
        day,
        hour,
        minute,
        second,
        microsecond,
        tzinfo,
        nanosecond,
        tz,
        unit,
        fold,
    ) -> None:
        gen_json.Timestamp(
            ts_input=ts_input,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond,
            tzinfo=tzinfo,
            nanosecond=nanosecond,
            tz=tz,
            unit=unit,
            fold=fold,
        )


class TestFuzzTimestampcombine(unittest.TestCase):
    @given(date=st.nothing(), time=st.nothing())
    def test_fuzz_Timestamp_combine(self, date, time) -> None:
        gen_json.Timestamp.combine(date=date, time=time)


class TestFuzzTimestampfromordinal(unittest.TestCase):
    @given(ordinal=st.integers(), tz=st.nothing())
    def test_fuzz_Timestamp_fromordinal(self, ordinal, tz) -> None:
        gen_json.Timestamp.fromordinal(ordinal=ordinal, tz=tz)


class TestFuzzTimestampfromtimestamp(unittest.TestCase):
    @given(ts=st.nothing(), tz=st.none())
    def test_fuzz_Timestamp_fromtimestamp(self, ts, tz) -> None:
        gen_json.Timestamp.fromtimestamp(ts=ts, tz=tz)


class TestFuzzTimestampnow(unittest.TestCase):
    @given(tz=st.one_of(st.none(), st.text()))
    def test_fuzz_Timestamp_now(self, tz) -> None:
        gen_json.Timestamp.now(tz=tz)


class TestFuzzTimestampstrptime(unittest.TestCase):
    @given(date_string=st.text(), format=st.nothing())
    def test_fuzz_Timestamp_strptime(self, date_string, format) -> None:
        gen_json.Timestamp.strptime(date_string=date_string, format=format)


class TestFuzzTimestamptoday(unittest.TestCase):
    @given(tz=st.one_of(st.none(), st.text()))
    def test_fuzz_Timestamp_today(self, tz) -> None:
        gen_json.Timestamp.today(tz=tz)


class TestFuzzTimestamputcfromtimestamp(unittest.TestCase):
    @given(ts=st.nothing())
    def test_fuzz_Timestamp_utcfromtimestamp(self, ts) -> None:
        gen_json.Timestamp.utcfromtimestamp(ts=ts)


class TestFuzzClean_Interval(unittest.TestCase):
    @given(
        interval=st.tuples(
            st.builds(Interval),
            st.sampled_from(gen_json.Dept),
            st.sampled_from(gen_json.DeptStatus),
        )
    )
    def test_fuzz_clean_interval(
        self, interval: tuple[pandas.Interval, gen_json.Dept, gen_json.DeptStatus]
    ) -> None:
        gen_json.clean_interval(interval=interval)


class TestFuzzCreate_Interval(unittest.TestCase):
    @given(
        start_date=st.from_type(pandas._libs.tslibs.timestamps.Timestamp),
        end_date=st.from_type(pandas._libs.tslibs.timestamps.Timestamp),
        dept=st.sampled_from(gen_json.Dept),
        status=st.sampled_from(gen_json.DeptStatus),
    )
    def test_fuzz_create_interval(
        self,
        start_date: gen_json.Timestamp,
        end_date: gen_json.Timestamp,
        dept: gen_json.Dept,
        status: gen_json.DeptStatus,
    ) -> None:
        gen_json.create_interval(
            start_date=start_date, end_date=end_date, dept=dept, status=status
        )


class TestFuzzGen_Interval_Data(unittest.TestCase):
    @given(
        data=st.one_of(st.none(), st.sets(st.sampled_from(gen_json.Dept))),
        approps_gap_flag=st.booleans(),
        depts_set=st.sets(st.sampled_from(gen_json.Dept)),
    )
    def test_fuzz_gen_interval_data(
        self,
        data: typing.Union[set[gen_json.Dept], None],
        approps_gap_flag: bool,
        depts_set: set[gen_json.Dept],
    ) -> None:
        gen_json.gen_interval_data(
            data=data, approps_gap_flag=approps_gap_flag, depts_set=depts_set
        )


class TestFuzzInsert_Gap_Intervals(unittest.TestCase):
    @given(dept=st.nothing(), intervals=st.nothing())
    def test_fuzz_insert_gap_intervals(self, dept, intervals) -> None:
        gen_json.insert_gap_intervals(dept=dept, intervals=intervals)


class TestFuzzInterval_To_Dict(unittest.TestCase):
    @given(interval=st.builds(Interval))
    def test_fuzz_interval_to_dict(self, interval: pandas.Interval) -> None:
        gen_json.interval_to_dict(interval=interval)


class TestFuzzProcess_Data_Entry(unittest.TestCase):
    @given(
        key=st.tuples(st.text(), st.text()),
        value=st.one_of(
            st.sets(st.sampled_from(gen_json.Dept)),
            st.tuples(
                st.one_of(st.none(), st.sets(st.sampled_from(gen_json.Dept))),
                st.sampled_from(gen_json.ShutdownFlag),
            ),
        ),
        approps_gap_flag=st.booleans(),
        depts_set=st.sets(st.sampled_from(gen_json.Dept)),
    )
    def test_fuzz_process_data_entry(
        self,
        key: tuple[str, str],
        value: typing.Union[
            set[gen_json.Dept],
            tuple[typing.Union[set[gen_json.Dept], None], gen_json.ShutdownFlag],
        ],
        approps_gap_flag: bool,
        depts_set: set[gen_json.Dept],
    ) -> None:
        gen_json.process_data_entry(
            key=key, value=value, approps_gap_flag=approps_gap_flag, depts_set=depts_set
        )


class TestFuzzSerialize_Intervals(unittest.TestCase):
    @given(
        intervals=st.tuples(
            st.builds(Interval),
            st.sampled_from(gen_json.Dept),
            st.sampled_from(gen_json.DeptStatus),
        )
    )
    def test_fuzz_serialize_intervals(
        self, intervals: tuple[pandas.Interval, gen_json.Dept, gen_json.DeptStatus]
    ) -> None:
        gen_json.serialize_intervals(intervals=intervals)


class TestFuzzUnique(unittest.TestCase):
    @given(enumeration=st.nothing())
    def test_fuzz_unique(self, enumeration) -> None:
        gen_json.unique(enumeration=enumeration)


class TestFuzzWrite_To_Json(unittest.TestCase):
    @given(
        data=st.lists(
            st.dictionaries(
                keys=st.dictionaries(keys=st.just("interval"), values=st.just("start")),
                values=st.text(),
            )
        ),
        filename=st.text(),
    )
    def test_fuzz_write_to_json(self, data, filename: str) -> None:
        gen_json.write_to_json(data=data, filename=filename)
