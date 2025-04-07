from __future__ import annotations

import ast
import dataclasses
import re
from enum import Enum, unique

import astor
import pandas as pd
from pandas import Timestamp


@unique
class Dept(Enum):
    """
    Dept enums represent federal departments and are used throughout fedcal to
    represent departments

    Attributes
    ----------
    abbrev
    full
    short

    """

    def __init__(self, abbreviation: str, full_name: str, short_name: str) -> None:
        """
        Initializes an instance of Dept, an enum for storing
        constants of federal executive branch departments.

        Args:
            abbreviation (str): The mixed case abbreviation of the department.
            full_name (str): The full name of the department in mixed case.
            short_name (str): The shortened name of the department in mix case.
        """
        self.abbrev: str = abbreviation  # mixed case abbreviation
        self.full: str = full_name  # full name in mixed case
        self.short: str = short_name  # shortened name in mixed case

    DHS = ("DHS", "Department of Homeland Security", "Homeland Security")
    DOC = ("DoC", "Department of Commerce", "Commerce")
    DOD = ("DoD", "Department of Defense", "Defense")
    DOE = ("DoE", "Department of Energy", "Energy")
    DOI = ("DoI", "Department of the Interior", "Interior")
    DOJ = ("DoJ", "Department of Justice", "Justice")
    DOL = ("DoL", "Department of Labor", "Labor")
    DOS = ("DoS", "Department of State", "State")
    DOT = ("DoT", "Department of Transportation", "Transportation")
    ED = ("ED", "Department of Education", "Education")
    HHS = (
        "HHS",
        "Department of Health and Human Services",
        "Health and Human Services",
    )
    HUD = (
        "HUD",
        "Department of Housing and Urban Development",
        "Housing and Urban Development",
    )
    IA = ("IA", "Independent Agencies", "Independent Agencies")
    PRES = ("PRES", "Executive Office of the President", "Office of the President")
    USDA = ("USDA", "Department of Agriculture", "Agriculture")
    USDT = ("USDT", "Department of the Treasury", "Treasury")
    VA = ("VA", "Department of Veterans Affairs", "Veterans Affairs")

    def __iter__(self):
        yield self.value


depts_set: set[Dept] = {
    Dept.DHS,
    Dept.DOC,
    Dept.DOD,
    Dept.DOE,
    Dept.DOI,
    Dept.DOJ,
    Dept.DOL,
    Dept.DOS,
    Dept.DOT,
    Dept.ED,
    Dept.HHS,
    Dept.HUD,
    Dept.IA,
    Dept.PRES,
    Dept.USDA,
    Dept.USDT,
    Dept.VA,
}

depts: list[Dept] = [
    Dept.DHS,
    Dept.DOC,
    Dept.DOD,
    Dept.DOE,
    Dept.DOI,
    Dept.DOJ,
    Dept.DOL,
    Dept.DOS,
    Dept.DOT,
    Dept.ED,
    Dept.HHS,
    Dept.HUD,
    Dept.IA,
    Dept.PRES,
    Dept.USDA,
    Dept.USDT,
    Dept.VA,
]
"""
depts_set: A set of top-level executive departments as enum
objects. Data currently omit judiciary and legislative budgets (federal courts
and Congress).
"""

dhs_formed: Timestamp = pd.to_datetime(arg="2002-11-25", format="ISO8601")


@unique
class DeptStatus(Enum):
    def __init__(
        self,
        value: int,
        variable_string: str,
        appropriations_status: str,
        operational_status: str,
        simple_status: str,
    ) -> None:
        self.val: int = value
        self.var: str = variable_string
        self.approps: str = appropriations_status
        self.ops: str = operational_status
        self.simple: str = simple_status

    FA = (4, "full_approps", "full appropriations", "open", "appropriated")
    ND = (
        3,
        "approps_cr_or_full",
        "appropriated but unknown if full_year or cr",
        "open, unknown capacity",
        "cr or full",
    )
    CR = (2, "cont_res", "continuing resolution", "open with limitations", "cr")
    GAP = (
        1,
        "approps_gap",
        "no appropriations",
        "minimally open",
        "appropriations gap",
    )
    SDN = (0, "shutdown", "no appropriations and shutdown", "shutdown", "shutdown")
    FUT = (
        -1,
        "future_unknown",
        "future status unknown",
        "future status unknown",
        "future",
    )


cr_data_cutoff = pd.Timestamp(year=1998, month=10, day=1)

# Note: For APPROPS_GAPS and CRs we don't base the intervals
# on bill timelines, but instead times when the departments were/are impacted,
# so if the same set of departments experienced a CR for a given period, even
# if under multiple bills with different expiration dates, it's the same group
# for our purposes. We're concerned with status here, not legislative nuance.
# I recognize impending funding deadlines can have a substantial impact on departments
# and we are eliminating that nuance with this approach, but this substantially
# simplifies implementation and ease of comprehension. If you have a better idea, open # an issue.


def mirror_diff(other: list[Dept], dhs: bool = True) -> list[Dept]:
    depts = depts_set if dhs else depts_set.difference({Dept.DHS})
    diff: set[Dept] = depts.difference(set(other))
    if diff:
        return sorted(list(diff), key=lambda x: (x.name, x.abbrev))
    else:
        return []


def drop_dhs(depts: set[Dept] | None = None) -> set[Dept]:
    """Simple function that drops DHS from pre-DHS data"""
    depts = depts or depts_set
    new_depts = depts.difference({Dept.DHS})
    assert Dept.DHS not in new_depts
    return new_depts


APPROPS_DATA = {
    ("1970-01-01", "1976-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1976-10-01", "1976-10-10"): [
        {DeptStatus.GAP: [Dept.HHS, Dept.ED, Dept.DOL]},
        {
            DeptStatus.ND: [
                [
                    Dept.DHS,
                    Dept.DOC,
                    Dept.DOD,
                    Dept.DOE,
                    Dept.DOI,
                    Dept.DOJ,
                    Dept.DOS,
                    Dept.DOT,
                    Dept.HUD,
                    Dept.IA,
                    Dept.PRES,
                    Dept.USDA,
                    Dept.USDT,
                    Dept.VA,
                ]
            ]
        },
    ],
    ("1976-10-11", "1977-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1977-10-01", "1977-10-12"): [
        {DeptStatus.GAP: [Dept.HHS, Dept.ED, Dept.DOL]},
        {
            DeptStatus.ND: [
                [
                    Dept.DHS,
                    Dept.DOC,
                    Dept.DOD,
                    Dept.DOE,
                    Dept.DOI,
                    Dept.DOJ,
                    Dept.DOS,
                    Dept.DOT,
                    Dept.HUD,
                    Dept.IA,
                    Dept.PRES,
                    Dept.USDA,
                    Dept.USDT,
                    Dept.VA,
                ]
            ]
        },
    ],
    ("1977-10-13", "1977-11-09"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1977-11-10", "1977-11-29"): [
        {DeptStatus.GAP: [Dept.HHS, Dept.ED, Dept.DOL]},
        {
            DeptStatus.ND: [
                [
                    Dept.DHS,
                    Dept.DOC,
                    Dept.DOD,
                    Dept.DOE,
                    Dept.DOI,
                    Dept.DOJ,
                    Dept.DOS,
                    Dept.DOT,
                    Dept.HUD,
                    Dept.IA,
                    Dept.PRES,
                    Dept.USDA,
                    Dept.USDT,
                    Dept.VA,
                ]
            ]
        },
    ],
    ("1977-11-30", "1978-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1978-10-01", "1978-10-17"): [
        {DeptStatus.GAP: [Dept.HHS, Dept.ED, Dept.DOD, Dept.DOL]},
        {
            DeptStatus.ND: [
                [
                    Dept.DHS,
                    Dept.DOC,
                    Dept.DOE,
                    Dept.DOI,
                    Dept.DOJ,
                    Dept.DOS,
                    Dept.DOT,
                    Dept.HUD,
                    Dept.IA,
                    Dept.PRES,
                    Dept.USDA,
                    Dept.USDT,
                    Dept.VA,
                ]
            ]
        },
    ],
    ("1978-10-18", "1979-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1979-10-01", "1979-10-11"): {
        DeptStatus.GAP: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1979-10-12", "1980-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1980-10-01", "1981-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1981-10-01", "1981-11-20"): {
        DeptStatus.CR: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1981-11-21", "1981-11-21"): {
        DeptStatus.SDN: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1981-11-22", "1982-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1982-10-01", "1982-12-18"): {
        DeptStatus.CR: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1982-12-18", "1982-12-20"): {
        DeptStatus.GAP: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1982-12-21", "1983-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1983-10-01", "1983-11-10"): {
        DeptStatus.CR: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1983-11-11", "1983-11-13"): {
        DeptStatus.GAP: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1983-11-14", "1984-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1984-10-01", "1984-10-03"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1984-10-04", "1984-10-15"): [
        {DeptStatus.SDN: [Dept.DOJ, Dept.IA, Dept.HUD, Dept.DOS]},
        {
            DeptStatus.ND: [
                [
                    Dept.DHS,
                    Dept.DOC,
                    Dept.DOD,
                    Dept.DOE,
                    Dept.DOI,
                    Dept.DOL,
                    Dept.DOT,
                    Dept.ED,
                    Dept.HHS,
                    Dept.PRES,
                    Dept.USDA,
                    Dept.USDT,
                    Dept.VA,
                ]
            ]
        },
    ],
    ("1984-10-16", "1986-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1986-10-01", "1986-10-16"): {
        DeptStatus.CR: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1986-10-17", "1986-10-17"): {
        DeptStatus.SDN: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1986-10-18", "1987-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1987-10-01", "1987-12-18"): {
        DeptStatus.CR: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1987-12-19", "1987-12-19"): {
        DeptStatus.GAP: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1987-12-20", "1990-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1990-10-01", "1990-10-05"): {
        DeptStatus.CR: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1990-10-06", "1990-10-08"): {
        DeptStatus.GAP: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1990-10-09", "1995-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1995-10-01", "1995-11-13"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1995-11-14", "1995-11-18"): [
        {
            DeptStatus.SDN: [
                Dept.DOD,
                Dept.DOL,
                Dept.DOT,
                Dept.HUD,
                Dept.PRES,
                Dept.ED,
                Dept.HHS,
                Dept.DOJ,
                Dept.IA,
                Dept.USDT,
                Dept.DOC,
                Dept.DOI,
                Dept.VA,
                Dept.DOS,
            ]
        },
        {DeptStatus.ND: [[Dept.DHS, Dept.DOE, Dept.USDA]]},
    ],
    ("1995-11-19", "1995-12-15"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1995-12-16", "1996-01-05"): [
        {
            DeptStatus.SDN: [
                Dept.HUD,
                Dept.PRES,
                Dept.DOL,
                Dept.DOT,
                Dept.ED,
                Dept.HHS,
                Dept.DOJ,
                Dept.IA,
                Dept.DOC,
                Dept.DOI,
                Dept.VA,
                Dept.DOS,
            ]
        },
        {DeptStatus.ND: [[Dept.DHS, Dept.DOD, Dept.DOE, Dept.USDA, Dept.USDT]]},
    ],
    ("1996-01-06", "1998-09-30"): {
        DeptStatus.ND: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1998-10-01", "1998-10-07"): {
        DeptStatus.CR: [
            Dept.DOE,
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOD,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1998-10-08", "1998-10-17"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("1998-10-08", "1999-09-30"): {DeptStatus.FA: [Dept.DOE]},
    ("1998-10-18", "1998-10-21"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("1998-10-18", "1999-09-30"): {DeptStatus.FA: [Dept.DOD]},
    ("1998-10-22", "1999-09-30"): {
        DeptStatus.FA: [
            Dept.DOT,
            Dept.ED,
            Dept.USDA,
            Dept.DOI,
            Dept.VA,
            Dept.DOL,
            Dept.HUD,
            Dept.PRES,
            Dept.HHS,
            Dept.IA,
            Dept.DOC,
            Dept.USDT,
            Dept.DOJ,
            Dept.DOS,
        ]
    },
    ("1999-10-01", "2000-09-30"): {DeptStatus.FA: [Dept.DOE, Dept.USDT]},
    ("1999-10-01", "1999-10-09"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.VA,
        ]
    },
    ("1999-10-10", "2000-09-30"): {DeptStatus.FA: [Dept.DOT]},
    ("1999-10-10", "1999-10-20"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.VA,
        ]
    },
    ("1999-10-21", "2000-09-30"): {DeptStatus.FA: [Dept.HUD, Dept.VA]},
    ("1999-10-21", "1999-10-22"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
        ]
    },
    ("1999-10-23", "2000-09-30"): {DeptStatus.FA: [Dept.USDA]},
    ("1999-10-23", "1999-10-25"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
        ]
    },
    ("1999-10-26", "2000-09-30"): {DeptStatus.FA: [Dept.DOD]},
    ("1999-10-26", "1999-11-29"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
        ]
    },
    ("1999-11-30", "2000-09-30"): {
        DeptStatus.FA: [
            Dept.DOC,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
        ]
    },
    ("2000-10-01", "2001-09-30"): {DeptStatus.FA: [Dept.DOD]},
    ("2000-10-01", "2000-10-11"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2000-10-12", "2001-09-30"): {DeptStatus.FA: [Dept.DOE, Dept.DOI, Dept.DOT]},
    ("2000-10-12", "2000-10-23"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2000-10-24", "2001-09-30"): {DeptStatus.FA: [Dept.HUD, Dept.VA]},
    ("2000-10-24", "2000-10-27"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
        ]
    },
    ("2000-10-28", "2001-09-30"): {DeptStatus.FA: [Dept.USDA]},
    ("2000-10-28", "2000-11-06"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
        ]
    },
    ("2000-11-07", "2001-09-30"): {DeptStatus.FA: [Dept.DOS]},
    ("2000-11-07", "2000-12-21"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOJ,
            Dept.DOL,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
        ]
    },
    ("2000-12-22", "2001-09-30"): {
        DeptStatus.FA: [
            Dept.DOC,
            Dept.DOJ,
            Dept.DOL,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
        ]
    },
    ("2001-10-01", "2001-11-05"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2001-11-06", "2002-09-30"): {DeptStatus.FA: [Dept.DOI]},
    ("2001-11-06", "2001-11-12"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2001-11-13", "2002-09-30"): {DeptStatus.FA: [Dept.DOE, Dept.USDT]},
    ("2001-11-13", "2001-11-26"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.VA,
        ]
    },
    ("2001-11-27", "2002-09-30"): {DeptStatus.FA: [Dept.HUD, Dept.VA]},
    ("2001-11-27", "2001-11-28"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
        ]
    },
    ("2001-11-29", "2002-09-30"): {
        DeptStatus.FA: [Dept.DOC, Dept.DOJ, Dept.DOS, Dept.USDA]
    },
    ("2001-11-29", "2001-12-18"): {
        DeptStatus.CR: [
            Dept.DOD,
            Dept.DOL,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
        ]
    },
    ("2001-12-19", "2002-09-30"): {DeptStatus.FA: [Dept.DOT]},
    ("2001-12-19", "2002-01-10"): {
        DeptStatus.CR: [Dept.DOD, Dept.DOL, Dept.ED, Dept.HHS, Dept.IA, Dept.PRES]
    },
    ("2002-01-11", "2002-09-30"): {
        DeptStatus.FA: [Dept.DOD, Dept.DOL, Dept.ED, Dept.HHS, Dept.IA, Dept.PRES]
    },
    ("2002-10-01", "2002-10-22"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2002-10-23", "2003-09-30"): {DeptStatus.FA: [Dept.DOD]},
    ("2002-10-23", "2002-11-24"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2002-11-25", "2003-02-20"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2003-02-21", "2003-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2003-10-01", "2004-09-30"): {DeptStatus.FA: [Dept.DHS, Dept.DOD]},
    ("2003-10-01", "2003-11-10"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2003-11-11", "2004-09-30"): {DeptStatus.FA: [Dept.DOI]},
    ("2003-11-11", "2003-12-01"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2003-12-02", "2004-09-30"): {DeptStatus.FA: [Dept.DOE]},
    ("2003-12-02", "2004-01-23"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2004-01-24", "2004-09-30"): {
        DeptStatus.FA: [
            Dept.DOC,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2004-10-01", "2005-09-30"): {DeptStatus.FA: [Dept.DOD]},
    ("2004-10-01", "2004-10-18"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2004-10-19", "2005-09-30"): {DeptStatus.FA: [Dept.DHS]},
    ("2004-10-19", "2004-12-08"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2004-12-09", "2005-09-30"): {
        DeptStatus.FA: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2005-10-01", "2006-09-30"): {DeptStatus.FA: [Dept.DOI]},
    ("2005-10-01", "2005-10-18"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2005-10-19", "2006-09-30"): {DeptStatus.FA: [Dept.DHS]},
    ("2005-10-19", "2005-11-10"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2005-11-11", "2006-09-30"): {DeptStatus.FA: [Dept.USDA]},
    ("2005-11-11", "2005-11-14"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2005-11-15", "2006-09-30"): {DeptStatus.FA: [Dept.DOS]},
    ("2005-11-15", "2005-11-19"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2005-11-20", "2006-09-30"): {DeptStatus.FA: [Dept.DOE]},
    ("2005-11-20", "2005-11-22"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2005-11-23", "2006-09-30"): {DeptStatus.FA: [Dept.DOC, Dept.DOJ]},
    ("2005-11-23", "2005-11-30"): {
        DeptStatus.CR: [
            Dept.DOD,
            Dept.DOL,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2005-12-01", "2006-09-30"): {
        DeptStatus.FA: [Dept.DOT, Dept.HUD, Dept.USDT, Dept.VA]
    },
    ("2005-12-01", "2005-12-30"): {
        DeptStatus.CR: [Dept.DOD, Dept.DOL, Dept.ED, Dept.HHS, Dept.IA, Dept.PRES]
    },
    ("2005-12-31", "2006-09-30"): {
        DeptStatus.FA: [Dept.DOD, Dept.DOL, Dept.ED, Dept.HHS, Dept.IA, Dept.PRES]
    },
    ("2006-10-01", "2007-09-30"): {DeptStatus.FA: [Dept.DOD]},
    ("2006-10-01", "2006-10-04"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2006-10-05", "2007-09-30"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2007-10-01", "2007-11-13"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2007-11-14", "2008-09-30"): {DeptStatus.FA: [Dept.DOD]},
    ("2007-11-14", "2007-12-26"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2007-12-27", "2008-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2008-10-01", "2009-09-30"): {DeptStatus.FA: [Dept.DHS, Dept.DOD, Dept.VA]},
    ("2008-10-01", "2009-03-11"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
        ]
    },
    ("2009-03-12", "2009-09-30"): {
        DeptStatus.FA: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
        ]
    },
    ("2009-10-01", "2009-10-21"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2009-10-22", "2010-09-30"): {DeptStatus.FA: [Dept.USDA]},
    ("2009-10-22", "2009-10-28"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2009-10-29", "2010-09-30"): {DeptStatus.FA: [Dept.DHS, Dept.DOE]},
    ("2009-10-29", "2009-10-30"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2009-10-31", "2010-09-30"): {DeptStatus.FA: [Dept.DOI]},
    ("2009-10-31", "2009-12-18"): {
        DeptStatus.CR: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2009-12-19", "2010-09-30"): {
        DeptStatus.FA: [
            Dept.DOC,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2009-12-19", "2009-12-19"): {DeptStatus.CR: [Dept.DOD, Dept.HHS]},
    ("2009-12-20", "2010-09-30"): {DeptStatus.FA: [Dept.DOD, Dept.HHS]},
    ("2010-10-01", "2011-04-15"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2011-04-16", "2011-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2011-10-01", "2011-11-18"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2011-11-19", "2012-09-30"): {
        DeptStatus.FA: [Dept.DOC, Dept.DOJ, Dept.DOT, Dept.HUD, Dept.USDA]
    },
    ("2011-11-19", "2011-12-23"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2011-12-24", "2012-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2012-10-01", "2013-03-26"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2013-03-27", "2013-09-30"): {
        DeptStatus.CR: [
            Dept.DOE,
            Dept.DOI,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
        ]
    },
    ("2013-10-01", "2013-10-16"): {
        DeptStatus.SDN: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2013-10-17", "2014-01-17"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2014-01-18", "2014-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2014-10-01", "2014-12-16"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2014-12-17", "2015-09-30"): {
        DeptStatus.FA: [
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2014-12-17", "2015-03-04"): {DeptStatus.CR: [Dept.DHS, Dept.HHS]},
    ("2015-03-05", "2015-09-30"): {DeptStatus.FA: [Dept.DHS, Dept.HHS]},
    ("2015-10-01", "2015-12-18"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2015-12-19", "2016-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2016-10-01", "2017-09-30"): {DeptStatus.FA: [Dept.VA]},
    ("2016-10-01", "2017-05-05"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
        ]
    },
    ("2017-05-06", "2017-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
        ]
    },
    ("2017-10-01", "2018-01-20"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2018-01-21", "2018-01-21"): {
        DeptStatus.SDN: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2018-01-22", "2018-03-23"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2018-03-24", "2018-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2018-10-01", "2019-09-30"): {
        DeptStatus.FA: [Dept.DOD, Dept.DOE, Dept.DOL, Dept.ED, Dept.HHS, Dept.VA]
    },
    ("2018-10-01", "2018-12-21"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOS,
            Dept.DOT,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
        ]
    },
    ("2018-12-22", "2019-02-09"): {
        DeptStatus.SDN: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOS,
            Dept.DOT,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
        ]
    },
    ("2019-02-10", "2019-02-15"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOS,
            Dept.DOT,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
        ]
    },
    ("2019-02-16", "2019-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOS,
            Dept.DOT,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
        ]
    },
    ("2019-10-01", "2019-12-20"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2019-12-21", "2020-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2020-10-01", "2020-12-27"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2020-12-28", "2021-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2021-10-01", "2022-03-15"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2022-03-16", "2022-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2022-10-01", "2022-12-29"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2022-12-30", "2023-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2023-10-01", "2024-03-09"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOC,
            Dept.DOD,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOL,
            Dept.DOS,
            Dept.DOT,
            Dept.ED,
            Dept.HHS,
            Dept.HUD,
            Dept.IA,
            Dept.PRES,
            Dept.USDA,
            Dept.USDT,
            Dept.VA,
        ]
    },
    ("2024-03-10", "2024-09-30"): {
        DeptStatus.FA: [
            Dept.DOC,
            Dept.DOE,
            Dept.DOI,
            Dept.DOJ,
            Dept.DOT,
            Dept.HUD,
            Dept.USDA,
            Dept.VA,
        ],
    },
    ("2024-03-10", "2024-03-23"): {
        DeptStatus.CR: [
            Dept.DHS,
            Dept.DOD,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
        ]
    },
    ("2024-03-24", "2024-09-30"): {
        DeptStatus.FA: [
            Dept.DHS,
            Dept.DOD,
            Dept.DOL,
            Dept.DOS,
            Dept.ED,
            Dept.HHS,
            Dept.IA,
            Dept.PRES,
            Dept.USDT,
        ]
    },
}


def enum_to_dict(enum_obj: Dept | DeptStatus):
    if not isinstance(enum_obj, tuple):
        return enum_obj.__class__.__name__ + "." + enum_obj.name


def convert_to_dict(obj):
    if isinstance(obj, dict):
        return {
            k if isinstance(k, tuple) else enum_to_dict(k): convert_to_dict(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [convert_to_dict(item) for item in obj]
    else:
        return enum_to_dict(obj)


@dataclasses.dataclass
class Store:
    old_end: pd.Timestamp = dataclasses.field(default=None)

    def set(self, val):
        self.old_end = val

    def get(self):
        return self.old_end

    def reset(self):
        self.old_end = None


New_APPROPS_DATA = {}

from datetime import datetime


# Function to convert string dates to datetime objects
def str_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


# Function to identify fiscal years and allocate initial statuses
def allocate_initial_statuses(data):
    fys = {}
    fy = None
    for date_range, departments in data.items():
        start_date, end_date = map(str_to_date, date_range)
        if start_date < str_to_date(date_str="1999-10-01"):
            continue
        if start_date.month == 10 and start_date.day == 1:
            fy_start = start_date
            fy_end = datetime(start_date.year + 1, 9, 30)
            fy = fy_end.year
        if fy not in fys.keys():
            fys[fy] = {}
        fys[fy][start_date, end_date] = data[
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        ]
    return fys


# Adjusting subsequent functions to utilize the fys information effectively
def adjust_intervals_and_handle_special_cases(fys):
    updated_data = {}
    deptset = depts_set.copy()
    for fy, items in fys.items():
        fa_set = set()
        cr_set = set()
        sdn_set = set()
        last_end = None
        fy_end = datetime(fy, 9, 30)
        sdn_end = None
        deptset = deptset if fy > 2003 else deptset.difference({Dept.DHS})
        for (s, e), itms in items.items():
            if pd.Timestamp(e) < dhs_formed:
                deptset.discard(Dept.DHS)
            else:
                deptset.add(Dept.DHS)
            status_keys = list(itms.keys())
            all_appropriated = (
                fa_set.union(cr_set)
                if fa_set and cr_set
                else fa_set
                if fa_set
                else cr_set
                if cr_set
                else set()
            )
            if (
                s.year > 2002
                or (s.year == 2002 and s.month > 11)
                or (s.year == 2002 and s.month == 11 and s.day >= 25)
            ):
                deptset = depts_set.copy()
                if Dept.DHS not in deptset:
                    deptset.update({Dept.DHS})
            if all_appropriated == deptset:
                sdn_set = set()
            if s.month == 10 and s.day == 1:
                if s.year > 2002:
                    deptset = depts_set.copy()
                if last_end:
                    last_end = None
                if fa_set or cr_set or sdn_set:
                    fa_set = set()
                    cr_set = set()
                    sdn_set = set()
                if sdn_end:
                    sdn_end = None
                if DeptStatus.SDN in status_keys:
                    if DeptStatus.FA in status_keys:
                        fa_set = set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        )
                        sdn_set = {
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.SDN, [])
                            if item not in fa_set
                        }
                        sdn_end = e
                        last_end = e if e != fy_end else None
                        updated_data.setdefault((s, fy_end), {})[
                            DeptStatus.FA
                        ] = sorted(list(fa_set), key=lambda x: x.name)
                        updated_data.setdefault((s, e), {})[DeptStatus.SDN] = sorted(
                            list(sdn_set), key=lambda x: x.name
                        )
                        if sdn_set:
                            if (
                                diff := deptset.difference(sdn_set).difference(fa_set)
                                if fa_set
                                else deptset.difference(sdn_set)
                            ):
                                updated_data.setdefault((s, e), {})[
                                    DeptStatus.CR
                                ] = sorted(list(diff), key=lambda x: x.name)
                        continue
                    elif DeptStatus.CR in status_keys:
                        cr_set = set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, [])
                        )
                        sdn_set = {
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.SDN, [])
                            if item not in cr_set
                        }
                        sdn_end = e
                        last_end = e
                        updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                            list(cr_set), key=lambda x: x.name
                        )
                        updated_data.setdefault((s, e), {})[DeptStatus.SDN] = sorted(
                            list(sdn_set), key=lambda x: x.name
                        )
                        if sdn_set:
                            if (
                                diff := deptset.difference(sdn_set).difference(cr_set)
                                if cr_set
                                else deptset.difference(sdn_set)
                            ):
                                updated_data.setdefault((s, e), {})[
                                    DeptStatus.FA
                                ] = sorted(list(diff), key=lambda x: x.name)
                        continue
                    else:
                        sdn_set = set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.SDN, [])
                        )
                        sdn_end = e
                        updated_data.setdefault((s, e), {})[DeptStatus.SDN] = sorted(
                            list(
                                fys.get(fy, {}).get((s, e), {}).get(DeptStatus.SDN, [])
                            ),
                            key=lambda x: x.name,
                        )

                        if sdn_set != deptset:
                            raise ValueError(
                                f" for key {(s, e)}, SDN set {sorted(list(x.name for x in sdn_set))} does not match deptset {sorted(list(x.name for x in deptset))} when no other possible statuses"
                            )
                        continue

                elif DeptStatus.FA in status_keys and DeptStatus.CR in status_keys:
                    fa_set = set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, []))
                    cr_set = set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, []))
                    updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                        list(cr_set), key=lambda x: x.name
                    )
                    if e != fy_end:
                        last_end = e
                    updated_data.setdefault((s, fy_end), {})[DeptStatus.FA] = sorted(
                        list(fa_set), key=lambda x: x.name
                    )
                    continue
                # We already eliminated SDN cases by now
                elif DeptStatus.FA in status_keys:
                    fa_set = set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, []))
                    cr_set = deptset.difference(fa_set or set())
                    if e != fy_end:
                        last_end = e
                    updated_data.setdefault((s, fy_end), {})[DeptStatus.FA] = sorted(
                        list(fa_set), key=lambda x: x.name
                    )
                    if fa_set and fa_set != deptset:
                        cr_set = deptset.difference(fa_set)
                        updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                            list(cr_set), key=lambda x: x.name
                        )
                    continue

                elif DeptStatus.CR in status_keys:
                    cr_set = set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, []))
                    fa_set = deptset.difference(cr_set) or set()
                    last_end = e
                    updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                        list(cr_set), key=lambda x: x.name
                    )
                    if fa_set:
                        updated_data.setdefault((s, fy_end), {})[
                            DeptStatus.FA
                        ] = sorted(list(fa_set), key=lambda x: x.name)
                    continue
                continue

            if not last_end and DeptStatus.SDN not in status_keys:
                if (
                    DeptStatus.FA in status_keys
                    and DeptStatus.CR in status_keys
                    and e != fy_end
                ):
                    updated_data.setdefault((s, fy_end), {})[DeptStatus.FA] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.FA, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        ),
                        key=lambda x: x.name,
                    )
                    updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.CR, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, [])
                        ),
                        key=lambda x: x.name,
                    )
                    if fa_set:
                        fa_set.update(
                            set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, []))
                        )
                    else:
                        fa_set = set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        )
                    if cr_set:
                        cr_set.update(
                            set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, []))
                        ).difference_update(fa_set)
                    else:
                        set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, [])
                        ).difference_update(fa_set)
                    last_end = e
                    continue
                elif e == fy_end:
                    updated_data[(s, e)] = fys[fy][(s, e)]
                    if DeptStatus.FA in status_keys:
                        updated_data.setdefault((s, fy_end), {})[
                            DeptStatus.FA
                        ] = sorted(
                            [
                                item
                                for item in fys.get(fy, {})
                                .get((s, e), {})
                                .get(DeptStatus.FA, [])
                                if item not in fa_set
                            ]
                            if fa_set
                            else list(
                                fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                            ),
                            key=lambda x: x.name,
                        )
                        fa_set.update(
                            set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, []))
                        )
                    if DeptStatus.CR in status_keys:
                        updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                            [
                                item
                                for item in fys.get(fy, {})
                                .get((s, e), {})
                                .get(DeptStatus.CR, [])
                                if item not in fa_set
                            ]
                        )
                        cr_set.update(
                            set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, []))
                        ).difference_update(fa_set)
                    continue
                elif DeptStatus.CR in status_keys:
                    updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.CR, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, []),
                        key=lambda x: x.name,
                    )
                    if cr := cr_set.union(
                        set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, []))
                    ):
                        cr_set = cr.difference(fa_set) if fa_set else cr
                    else:
                        cr_set = set()
                    last_end = e
                    continue

            elif (
                sdn_end
                and DeptStatus.SDN not in status_keys
                and (DeptStatus.FA in status_keys or DeptStatus.CR in status_keys)
            ):
                if DeptStatus.FA in status_keys and DeptStatus.CR not in status_keys:
                    updated_data.setdefault((s, fy_end), {})[DeptStatus.FA] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.FA, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        ),
                        key=lambda x: x.name,
                    )
                    if fa_set:
                        fa_set.update(
                            set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, []))
                        )
                    else:
                        fa_set = set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        )
                    if sdn_set:
                        sdn_set.difference_update(fa_set)
                    else:
                        sdn_set = set()
                    last_end = e if e != fy_end else None
                    if e >= sdn_end:
                        sdn_end = None
                    if (
                        fa_set.union(sdn_set)
                        if fa_set and sdn_set
                        else (fa_set or sdn_set) != deptset
                    ):
                        cr_set = deptset.difference(fa_set or set()).difference(sdn_set)
                        updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                            list(cr_set), key=lambda x: x.name
                        )
                    if fa_set and fa_set == deptset:
                        sdn_set = set()
                        cr_set = set()
                    if sdn_set and sdn_set == deptset:
                        fa_set = set()
                        cr_set = set()
                        sdn_end = e
                    if not sdn_set:
                        sdn_end = None
                    continue
                elif DeptStatus.CR in status_keys and DeptStatus.FA not in status_keys:
                    updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.CR, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, [])
                        ),
                        key=lambda x: x.name,
                    )
                    if fa_set:
                        cr_set = (
                            cr_set.union(
                                set(
                                    fys.get(fy, {})
                                    .get((s, e), {})
                                    .get(DeptStatus.CR, [])
                                )
                            ).difference(fa_set)
                            if cr_set
                            else set(
                                fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, [])
                            ).difference(fa_set)
                        )
                    else:
                        cr_set = (
                            cr_set.union(
                                set(
                                    fys.get(fy, {})
                                    .get((s, e), {})
                                    .get(DeptStatus.CR, [])
                                )
                            )
                            if cr_set
                            else set(
                                fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, [])
                            )
                        )
                    sdn_set.difference_update(cr_set)
                    last_end = e if e != fy_end else None
                    if e >= sdn_end:
                        sdn_end = None
                    if diff := deptset.difference(sdn_set or set()).difference(cr_set):
                        updated_data.setdefault((s, fy_end), {})[
                            DeptStatus.FA
                        ] = sorted(
                            [item for item in diff if item not in fa_set]
                            if fa_set
                            else list(diff),
                            key=lambda x: x.name,
                        )
                        fa_set.update(diff)
                    if not sdn_set:
                        sdn_end = None
                    continue
                else:
                    last_end = e
                    updated_data.setdefault((s, fy_end), {})[DeptStatus.FA] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.FA, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        ),
                        key=lambda x: x.name,
                    )
                    fa_set.update(
                        set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, []))
                    )
                    updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.CR, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, [])
                        ),
                        key=lambda x: x.name,
                    )
                    if not sdn_set:
                        sdn_end = None
                    continue

            elif sdn_end and DeptStatus.SDN in status_keys:
                sdn_set = set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.SDN, []))
                if DeptStatus.FA in status_keys:
                    updated_data.setdefault((s, fy_end), {})[DeptStatus.FA] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.FA, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        ),
                        key=lambda x: x.name,
                    )
                    fa_set.update(
                        set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, []))
                    )
                    sdn_set = (
                        sdn_set.difference_update(fa_set)
                        if sdn_set
                        else set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.SDN, [])
                        )
                    )
                    last_end = e if e != fy_end else None
                    sdn_end = last_end
                    if sdn_set and fa_set:
                        if sdn_set.union(fa_set) == deptset:
                            cr_set = set()
                    elif sdn_set or fa_set and (sdn_set or fa_set) == deptset:
                        cr_set = set()

                if diff := deptset.difference(sdn_set or set()).difference(fa_set):
                    updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                        [item for item in diff if item not in fa_set]
                        if fa_set
                        else list(diff),
                        key=lambda x: x.name,
                    )
                    cr_set = (
                        set(diff)
                        if not fa_set
                        else set([item for item in diff if item not in fa_set])
                    )
                    sdn_set.difference_update(cr_set)
                    last_end = e if e != fy_end else None
                    if sdn_set:
                        if cr_set:
                            sdn_set = set(
                                [item for item in sdn_set if item not in cr_set]
                            )
                        if fa_set:
                            sdn_set = set(
                                [item for item in sdn_set if item not in fa_set]
                            )

                updated_data.setdefault((s, e), {})[DeptStatus.SDN] = (
                    sorted(list(sdn_set), key=lambda x: x.name) if sdn_set else []
                )
                sdn_end = e if sdn_set else None
                continue

            elif DeptStatus.SDN in status_keys:
                sdn_set = set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.SDN, []))
                if DeptStatus.FA in status_keys:
                    updated_data.setdefault((s, fy_end), {})[DeptStatus.FA] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.FA, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        ),
                        key=lambda x: x.name,
                    )
                    if fa_set:
                        fa_set.update(
                            set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, []))
                        )
                    else:
                        fa_set = set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        )
                    sdn_set.difference_update(fa_set) if fa_set else sdn_set
                else:
                    if fa_set:
                        sdn_set.difference_update(fa_set)
                    else:
                        sdn_set = sdn_set or set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.SDN, [])
                        )
                    last_end = e if e != fy_end else None
                    sdn_end = last_end
                    if (sdn_set and fa_set and sdn_set.union(fa_set) == deptset) or (
                        (sdn_set or fa_set) and (sdn_set or fa_set) == deptset
                    ):
                        cr_set = set()
                    updated_data.setdefault((s, e), {})[DeptStatus.SDN] = (
                        sorted(list(sdn_set), key=lambda x: x.name) if sdn_set else []
                    )

                if (
                    sdn_set.union(fa_set) != deptset
                    if sdn_set and fa_set
                    else (sdn_set or fa_set) != deptset
                ):
                    diff = (sdn_set.union(fa_set) or sdn_set or fa_set).difference(
                        deptset
                    )
                    updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                        [item for item in diff if item not in fa_set or sdn_set]
                        if fa_set and sdn_set
                        else [
                            item for item in deptset if item not in (sdn_set or fa_set)
                        ],
                        key=lambda x: x.name,
                    )
                    cr_set = set(updated_data[(s, e)][DeptStatus.CR])
                    if sdn_set:
                        sdn_set.difference_update(cr_set)
                    else:
                        sdn_set = set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.SDN, [])
                        )
                if sdn_set and fa_set and sdn_set.union(fa_set) == deptset:
                    cr_set = set()
                if fa_set and not sdn_set and fa_set == deptset:
                    cr_set = set()
                if not sdn_set:
                    sdn_set = set()
                continue

            elif last_end:
                if DeptStatus.FA in status_keys:
                    updated_data.setdefault((s, fy_end), {})[DeptStatus.FA] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.FA, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        ),
                        key=lambda x: x.name,
                    )
                    if fa_set:
                        fa_set.update(
                            set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, []))
                        )
                    else:
                        fa_set = set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.FA, [])
                        )
                    last_end = e if e != fy_end else last_end
                    if sdn_end:
                        if last_end >= sdn_end:
                            sdn_end = None
                    if DeptStatus.CR not in status_keys and fa_set != deptset:
                        updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                            [
                                item
                                for item in deptset.difference(fa_set)
                                if item not in fa_set
                            ],
                            key=lambda x: x.name,
                        )
                        cr_set = set(updated_data[(s, e)][DeptStatus.CR])
                if DeptStatus.CR in status_keys:
                    updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                        [
                            item
                            for item in fys.get(fy, {})
                            .get((s, e), {})
                            .get(DeptStatus.CR, [])
                            if item not in fa_set
                        ]
                        if fa_set
                        else list(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, [])
                        ),
                        key=lambda x: x.name,
                    )
                    if cr_set and fa_set:
                        cr_set.update(
                            set(fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, []))
                        ).difference_update(fa_set)
                    elif cr_set:
                        cr_set = set(
                            fys.get(fy, {}).get((s, e), {}).get(DeptStatus.CR, [])
                        )
                if sdn_set:
                    sdn_set.difference_update(fa_set) if fa_set else sdn_set
                    if (sdn_set and fa_set and sdn_set.union(fa_set) == deptset) or (
                        (sdn_set or fa_set) and (sdn_set or fa_set) == deptset
                    ):
                        cr_set = set()
                    sdn_end = last_end
                    if not sdn_set:
                        sdn_end = None
                    else:
                        if diff := deptset.difference(
                            (fa_set).union(sdn_set)
                            if fa_set and sdn_set
                            else deptset.difference(fa_set or sdn_set)
                        ):
                            updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                                [item for item in diff if item not in fa_set]
                                if fa_set
                                else list(diff),
                                key=lambda x: x.name,
                            )
                            if cr_set:
                                if cr_diff := cr_set.union(diff):
                                    if fa_set:
                                        cr_set.update(cr_diff).difference_update(fa_set)
                                else:
                                    cr_set.update(cr_diff)
                            else:
                                cr_set = set(diff)
                            updated_data.setdefault((s, e), {})[DeptStatus.CR] = sorted(
                                list(cr_set) if cr_set else [], key=lambda x: x.name
                            )
                else:
                    depts_accounting = set()
                    if status_dict := updated_data.get((s, e), {}):
                        for v in status_dict.values():
                            depts_accounting.update(set(v))
                    if depts_accounting == deptset:
                        continue
                    if DeptStatus.FA in status_keys:
                        if fas := updated_data.get((s, fy_end), {}).get(
                            DeptStatus.FA, []
                        ):
                            depts_accounting.update(set(fas))
                        if depts_accounting == deptset:
                            continue
                    else:
                        print(
                            f"We appeared to have missed something. \n Key: {(s,e)}, \n status_keys = {status_keys} \n possibly missing: {set(d.name for d in deptset.difference(depts_accounting) if depts_accounting) or set(d.name for d in deptset)}"
                        )

    cp = {}
    for s, e in updated_data.keys():
        ns = pd.to_datetime(s).strftime("%Y-%m-%d")
        ne = pd.to_datetime(e).strftime("%Y-%m-%d")
        cp[ns, ne] = updated_data[s, e]
    final = {}
    for key, val in cp.items():
        for k, v in val.items():
            if v:
                final.setdefault(key, {})[k] = v
    return final


def sort_complex_dict(input_dict):
    # Sort the outer dictionary by the tuple keys
    sorted_dict = dict(
        sorted(
            input_dict.items(),
            key=lambda item: (pd.Timestamp(item[0][0]), pd.Timestamp(item[0][1])),
        )
    )

    # Sort the inner dictionaries and their lists
    for key, inner_dict in sorted_dict.items():
        # Sort the inner dictionary by its keys
        sorted_inner_dict = dict(
            sorted(inner_dict.items(), key=lambda item: (item[0].val, item[1]))
        )

        # Sort each list in the inner dictionary
        for inner_key, inner_list in sorted_inner_dict.items():
            sorted_inner_dict[inner_key] = sorted(
                inner_list, key=lambda x: (x.name, x.abbrev)
            )

        # Update the outer dictionary with the sorted inner dictionary
        sorted_dict[key] = sorted_inner_dict

    return sorted_dict


def interval_to_dict(interval) -> dict[str, str]:
    """
    Convert an interval to a dictionary for writing to JSON.

    Parameters
    ----------
        interval: The interval to convert.

    Returns
    -------
        A dictionary with "start" and "end" keys representing the left and right attributes of the interval, respectively.
    """
    return {"start": interval.left.isoformat(), "end": interval.right.isoformat()}


def serialize_intervals(intervals):
    """
    Serialize the intervals into a JSON-compatible format.

    Parameters
    ----------
        intervals: The intervals to serialize.

    Returns
    -------
        A list of dictionaries representing the serialized intervals.
    """
    return [
        {
            "interval": interval_to_dict(interval=interval),
            "dept": dept.name,
            "status": status.name,
        }
        for interval, dept, status in intervals
    ]


def write_to_json(data, filename: str) -> None:
    """
    Write the data to a JSON file.

    Parameters
    ----------
        data: The data to write.
        filename: The name of the file to write to.
    """
    with open(file=filename, mode="w") as file:
        json.dump(obj=data, fp=file, indent=4)


# Adjusting the function calls for execution
# fys = allocate_initial_statuses(APPROPS_DATA)
# final_data = adjust_intervals_and_handle_special_cases(fys)

code = convert_to_dict(APPROPS_DATA)
code = sort_complex_dict(code)

code_str = astor.to_source(
    ast.Module(
        body=[
            ast.Assign(
                targets=[ast.Name(id="APPROPS_DATA", ctx=ast.Store())],
                value=ast.Constant(value=code),
            )
        ]
    )
)

code_str = re.sub(
    pattern=r"(?:')(DeptStatus.[A-Z]{2,3}|Dept.[A-Z]{2,4})(?:')",
    repl=r"\1",
    string=code_str,
)


with open("dict.txt", "w") as f:
    f.write(code)
