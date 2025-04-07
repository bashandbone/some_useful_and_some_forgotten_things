# fedcal __init__.py
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
Welcome to fedcal!

fedcal's __init__.py. Nothing extraordinary here. We import and name the
primary API modules, `FedIndex` and `FedStamp` and their helper functions,
`to_fedstamp` and `to_fedindex`. This makes them easy to import and use, like:

```python
import fedcal as fc
dates = (1999,10,1), (2040,9,30)
fdx = fc.to_fedindex(dates)
```
"""

from ._base import MagicDelegator
from .enum import Dept, DeptStatus, DoW, Month

# from .fedindex import FedIndex, to_fedindex
# from .fedstamp import FedStamp, to_fedstamp
from .fiscal import FedFiscalCal
from .offsets import (
    FedBusinessDay,
    FedHolidays,
    FedPayDay,
    MilitaryPassDay,
    MilitaryPayDay,
)

# from .status import GovStatus
from .utils import (
    dt64_to_date,
    dt64_to_dow,
    iso_to_ts,
    to_datetimeindex,
    to_dt64,
    to_timestamp,
)

__all__: list[str] = [
    "Dept",
    "DeptStatus",
    "DoW",
    "FedBusinessDay",
    "FedFiscalCal",
    "FedHolidays",
    #    "FedIndex",
    "FedPayDay",
    #    "FedStamp",
    "GovStatus",
    "MagicDelegator",
    "MilitaryPassDay",
    "MilitaryPayDay",
    "Month",
    "dt64_to_date",
    "dt64_to_dow",
    "iso_to_ts",
    "to_datetimeindex",
    "to_dt64",
    #    "to_fedindex",
    #    "to_fedstamp",
    "to_timestamp",
]
