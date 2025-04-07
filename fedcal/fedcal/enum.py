# fedcal enum.py
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
Enum classes that support front and back-end department status retrieval and
delivery, ensuring consistency across modules thanks to their Enumy-ness.
"""
from __future__ import annotations

from enum import Enum, IntEnum, unique
from typing import Iterable, Type

from fedcal._base import EnumBase, HandyEnumMixin
from fedcal._typing import EnumType


@unique
class DoW(HandyEnumMixin, IntEnum):
    """
    Enum for days of the week.
    """

    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6

    def __str__(self) -> str:
        return self.name.lower()


@unique
class Month(HandyEnumMixin, IntEnum):
    """
    Enum for months.
    """

    JAN = 1
    FEB = 2
    MAR = 3
    APR = 4
    MAY = 5
    JUN = 6
    JUL = 7
    AUG = 8
    SEP = 9
    OCT = 10
    NOV = 11
    DEC = 12

    def __str__(self) -> str:
        return self.name.title()


@unique
class Dept(EnumBase, HandyEnumMixin, Enum):
    """
    Dept enums represent federal departments and are used throughout fedcal to
    represent departments

    Methods
    ----------
    reverse_lookup(cls, lookup_attr: str | int) -> EnumType:
        inherited from EnumBase. Allows reverse_lookup of enum members from
        their attributes.
        Example:
            ```python
            DeptStatus.reverse_lookup(3) # or "open, unknown capacity", etc
            >> DeptStatus.ND
            ```

    swap_attrs(cls, swap_attr: str, new_value: str) -> EnumType:)
        A shortcut method that uses reverse_lookup to swap attributes for a
        member. You give it one attribute representation of a member and it
        gives you another (you provide the desired new attribute as a string)
        Example:
            ```python
            Dept.Status.swap_attrs("appropriated", "val")
            >> 4
            ```


    """

    def __init__(self, abbreviation: str, full_name: str, short_name: str) -> None:
        """
        Initializes an instance of Dept, an enum for storing
        constants of federal executive branch departments.

        Attributes
        ----------
        abbrev (str): The mixed case abbreviation of the department.
        full (str): The full name of the department in mixed case.
        short (str): The shortened name of the department in mix case.
        """
        self.abbrev: str = abbreviation  # mixed case abbreviation
        self.full: str = full_name  # full name in mixed case
        self.short: str = short_name  # shortened name in mixed case

    def __str__(self) -> str:
        """
        Customized string representation of enum

        Returns
        -------
        Returns member's full name with abbreviation in parens
        (e.g. "Department of State (DoS)")
        """
        return f"{type(self).__name__}: {self.full} ({self.abbrev})"

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

    @classmethod
    def _lookup_attributes(cls: Type[EnumType]) -> Iterable[str]:
        """
        Returns a list of attributes for lookup.
        Implements EnumBase reverse_lookup and
        swap_attrs class methods.

        Returns
        -------
        list[str]: List of attributes for lookup.
        """
        return ["abbrev", "full", "short"]


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

"""
depts_set: A set of top-level executive departments as enum
objects. Data currently omit judiciary and legislative budgets (federal courts
and Congress).
"""


@unique
class DeptStatus(EnumBase, HandyEnumMixin, Enum):
    """
    DeptStatus is an enum used primarily for consistency across back-end
    operations to consistently apply and translate statuses for various uses.

    Methods
    ----------
    reverse_lookup(cls, lookup_attr: str | int) -> EnumType:
        inherited from EnumBase. Allows reverse_lookup of enum members from
        their attributes.
        Example:
            ```python
            DeptStatus.reverse_lookup(3) # or "open, unknown capacity", etc
            >> DeptStatus.ND
            ```

    swap_attrs(cls, swap_attr: str, new_value: str) -> EnumType:)
        A shortcut method that uses reverse_lookup to swap attributes for a
        member. You give it one attribute representation of a member and it
        gives you another (you provide the desired new attribute as a string)
        Example:
            ```python
            Dept.Status.swap_attrs("appropriated", "val")
            >> 4
            ```
    """

    def __init__(
        self,
        val: int,
        variable_string: str,
        appropriations_status: str,
        operational_status: str,
        simple_status: str,
    ) -> None:
        """
        We initialize additional enum attributes

        Attributes
        ----------
        val: ordered integer value of the status
        var: variable-style string representation of the status
        approps: string description of the associated appropriations status
        ops: string descrition of the operational status corresponding to the
        appropriations status
        simple_status: simplified status descriptor (as a string)
        """
        self.val: int = val
        self.var: str = variable_string
        self.approps: str = appropriations_status
        self.ops: str = operational_status
        self.simple: str = simple_status

    def __str__(self) -> str:
        """
        Customized string representation of enum

        Returns
        -------
        Returns simple status string with object name
        """
        return f"{type(self).__name__}: {self.simple}"

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
    SD = (0, "shutdown", "no appropriations and shutdown", "shutdown", "shutdown")
    FUT = (
        -1,
        "future_unknown",
        "future status unknown",
        "future status unknown",
        "future",
    )

    @classmethod
    def _lookup_attributes(cls: Type[EnumType]) -> Iterable[str]:
        """
        Implements `EnumBase` reverse_lookup and swap_attrs
        class methods.

        Returns
        -------
        list[str]: List of attributes for lookup.
        """
        return ["val", "var", "approps", "ops", "simple"]


__all__: list[str] = ["DoW", "Month", "Dept", "DeptStatus"]
