from __future__ import annotations

from enum import Enum, unique

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
    ("2023-10-01", "2024-03-01"): {
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
