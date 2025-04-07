# fedcal _base.py
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
_base is an internal support module containing the meta and base classes.
It consists of:
- MagicDelegator, a metaclass that facilitates cloning magic/dunder methods
- EnumBase, a base class for enumerated types that provides magic methods and
common class methods
- HandyEnumMixin, a mixin class for enumerated types that provides common
and useful class methods
"""

import inspect
from functools import total_ordering
from typing import Any, Callable, Generator, Iterable, Mapping, Type

from fedcal._typing import EnumType


class MagicDelegator(type):

    """
    Right now this is a machete vice scalpel approach. As we implement
    the pandas extension API, we may not need this or can scale it down
    considerably.

    `MagicDelegator` is a metaclass that facilitates cloning magic/dunder
    methods from the target class, which is `pd.Timestamp` for `FedStamp`
    and `pd.DatetimeIndex` for `FedIndex`. This allows us to maintain
    compositional principles, and avoid writing excessive boilerplate.
    Essentially, all we do here is check for magic methods not in the
    child class (i.e. `FedStamp`) and clone them from the target class
    (i.e. `pd.Timestamp`).

    Coupled with attribute delegation to the target class,
    this metaclass enables `FedStamp` and `FedIndex` to
    act as if they were `pd.Timestamp` and `pd.DatetimeIndex`, respectively,
    and seamlessly integrate into pandas operations.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        dct: dict[str, Any],
        delegate_to: str | None = None,
        delegate_class: type | None = None,
    ) -> Any:
        """
        Generates a new class with the magic methods cloned from the
        target class.

        Parameters
        ----------
        name
            class name
        bases
            any base classes as a tuple
        dct
            class dictionary

        **delegate_to** (class argument)
            name of new class's target attribute to delegate magic methods to
            (e.g. 'timestamp' for `FedStamp`), by default None
        **delegate_class** (class argument)
            name of the , by default None

        Returns
        -------
            New class (i.e. `FedStamp`) with magic methods cloned from
            target class for target attribute.

        Raises
        ------
        TypeError
            Raises TypeError is delegate_to or delegate_class are None.
        """
        if delegate_to is None or delegate_class is None:
            raise TypeError(
                "MagicDelegator requires 'delegate_to' attribute name and  "
                "'delegate_class'"
            )

        @staticmethod
        def create_magic_method(method_name: str) -> Callable[..., Any]:
            """
            Static method used to create magic methods from the target class.

            Parameters
            ----------
            method_name
            Name of the magic method (e.g. `__eq__`)

            Returns
            -------
                Cloned magic method.
            """

            def magic_method(self, *args, **kwargs) -> Any:
                """
                Helper method to call the magic method from the target class.
                This is used to create the magic methods for the new class
                (e.g. we take `pd.Timestamp`'s `__eq__` and clone it for
                `FedStamp`).

                Parameters
                ----------
                self
                    The instance of the new class.
                *args
                    Positional arguments to pass to the magic method.
                **kwargs
                    Keyword arguments to pass to the magic method.
                    (e.g. `FedStamp.__eq__(self, other)`)


                Returns
                -------
                Any
                    Returns the result of the magic method call.

                Raises
                ------
                AttributeError
                    Raises AttributeError if an attribute name cannot be found
                    in the new class's instance.
                AttributeError
                    Raises AttributeError if the method name cannot be found
                    in the target class.

                """
                if delegate_to not in self.__dict__:
                    raise AttributeError(
                        f"Attribute '{delegate_to}' not found in {self}"
                    )

                delegated_attr = self.__dict__[delegate_to]
                method = getattr(delegated_attr, method_name)
                return method(*args, **kwargs)

            return magic_method

        excluded_methods: set[str] = {
            "__class__",
            "__del__",
            "__dict__",
            "__dir__",
            "__doc__",
            "__getattr__",
            "__getattribute__",
            "__getstate__",
            "__hash__",
            "__init__",
            "__init_subclass__",
            "__new__",
            "__reduce__",
            "__reduce_cython__",
            "__reduce_ex__",
            "__repr__",
            "__setattr__",
            "__setstate__",
            "__setstate_cython__",
            "__subclasshook",
        }
        magic_methods: list[str] = [
            name
            for name, _ in inspect.getmembers(delegate_class, inspect.isroutine)
            if name.startswith("__")
            and name.endswith("__")
            and name not in excluded_methods
        ]

        for method_name in magic_methods:
            if method_name not in dct:
                dct[method_name] = create_magic_method(method_name=method_name)

        return super().__new__(mcs, name, bases, dct)


@total_ordering
class EnumBase:
    """
    EnumBase is a base class for enum classes that inherit from
    `EnumBase` and defines magic methods and common class methods for lookups
    and comparisons.
    """

    def __eq__(self, other: Any) -> bool:
        """
        Magic method to compare two enum values.

        Parameters
        ----------
        other
            The other enum value to compare to.

        Returns
        -------
        bool
            True if the enum values are equal, False otherwise.
        """
        return self.value == other.value and isinstance(other, type(self).__name__)

    def __lt__(self, other: Any) -> bool:
        """
        Magic method to compare two enum values.

        Parameters
        ----------
        other
            The other enum value to compare to.

        Returns
        -------
        bool
            True if the enum value is less than the other value, False
            otherwise.
        """
        return self.value < other.value and isinstance(other, type(self).__name__)

    def __hash__(self) -> int:
        """
        Simple hash implementation.

        Returns
        -------
            hash
        """
        return hash(self.value)

    def __iter__(self) -> Generator[str, Any, None]:
        """
        Iterates through the enum object's attributes.
        Returns a generator that yields the enum object's attributes.
        Requires _lookup_attributes to be implemented.

        Yields
        ------
            str | int: The enum object's attributes.

        """
        for attr in type(self)._lookup_attributes():
            yield getattr(self, attr)


class HandyEnumMixin:
    @classmethod
    def _lookup_attributes(cls: Type[EnumType]) -> Iterable[str]:
        """
        Child classes should override this method to return the attribute names
        that should be considered in the reverse lookup.
        """
        raise NotImplementedError("This method should be implemented by child classes.")

    @classmethod
    def reverse_lookup(
        cls: Type[EnumType], value: str | int, attributes: Iterable[str] = None
    ) -> EnumType | None:
        """
        Reverse lookup for enum object member from an attribute value. Child
        classes must implement cls._lookup_attributes().
        """
        attributes = attributes or cls._lookup_attributes()
        return next(
            (
                member
                for member in cls
                if any(getattr(member, attr, None) == value for attr in attributes)
            ),
            None,
        )

    @classmethod
    def swap_attr(cls: Type[EnumType], val: Any, rtn_attr: str) -> Any:
        """
        Method to swap one attribute value for another. Child
        classes must implement cls._lookup_attributes().
        """
        member = cls.reverse_lookup(val, attributes=cls._lookup_attributes())
        return getattr(member, rtn_attr, None) if member else None

    @classmethod
    def list_vals(cls) -> list[int | str]:
        """
        Simple classmethod to return the values of members.
        """
        return sorted(list(map(lambda c: c.value, cls)))

    @classmethod
    def list_by_attr(cls, attr: str) -> list[Any]:
        """
        Simple classmethod to return the attributes of members.
        """
        return sorted([member.attr for member in cls.members()])

    @classmethod
    def list_member_attrs(cls, member: EnumType) -> list[Any]:
        """
        Simple classmethod to return the attributes of members.
        """
        return sorted(
            member.value
            + ([getattr(member, attr) for attr in cls._lookup_attributes()])
        )

    @classmethod
    def members(cls) -> list[Type[EnumType]]:
        """
        Simple classmethod to return the members of the enum class.
        """
        return sorted(list(cls.__members__))

    @classmethod
    def zip(cls) -> list[tuple[Any]]:
        """
        Classmethod to return a list of tuples containing the enum class
        members and their values. The list is sorted by the enum class
        member values.

        Returns
        -------
            sorted list of member tuples
        """
        return sorted(zip(cls.__members__.items()), key=lambda k: k[0].value)

    @classmethod
    def map(cls) -> Mapping[Any, Any]:
        """
        Classmethod to return a map of member names to their values.

        Returns
        -------
            sorted mapping of member names to member values.
        """
        return dict(zip(cls._member_names_, cls._value2member_map_.keys()))

    @classmethod
    def val_attr_map(cls) -> Mapping[Any, Any]:
        """
        Maps member values (as keys) to the members' attributes.

        Returns
        -------
            Returns dictionary map of member' values to its attributes
        """
        member_attrs = [
            cls.list_member_attrs(member=x) if x in cls._member_names_ else None
            for x in cls._member_names_
        ]
        return dict(
            zip(cls._member_names_, cls._value2member_map_.values(), member_attrs)
        )

    @classmethod
    def attr_member_map(cls, attr: str) -> Mapping[Any, Any]:
        return {
            getattr(cls.members(), attr): item for item in cls.val_attr_map().items()
        }

    @classmethod
    def get_reverse_member_value_map(cls) -> Mapping[Any, Any]:
        return cls._value2member_map_

    @classmethod
    def member_dict(cls) -> Mapping[Any, Any]:
        members = cls.members()
        return {member: cls.list_member_attrs(member=member) for member in members}


__all__: list[str] = ["EnumBase", "HandyEnumMixin", "MagicDelegator"]
