#!/usr/bin/env python3
"""
Copyright 2024 Adam Poulemanos

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import logging
import logging.config
import os
import shutil
import sys
import time
import tomllib


from attrs import define, field
from base64 import b64encode
from hashlib import sha256
import gi
gi.require_version(namespace='Gio', version='2.0')
gi.require_version(namespace='Gck', version='2.0')
from gi.repository import Gio, GLib, Gck
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

import secretstorage

# tomli_w imported as needed in Config.write_default_config()

if TYPE_CHECKING:
    from gi.overrides.GLib import Variant
    from subprocess import CompletedProcess
    from jeepney.io.blocking import DBusConnection

logger = logging.getLogger(__name__)

ClevisSettingsType = dict[
    str, str | dict[str, str | int | list[str | int | None]] | None
]
ConfigType = dict[str, str | int | ClevisSettingsType]

app_name = "AutoKeyring"
app_name_lower = app_name.lower()

def set_logging_config() -> None:
    logging.config.dictConfig(
        config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {"format": "%(asctime)s %(levelname)-4s %(message)s"}
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                },
            },
            "root": {"level": "DEBUG", "handlers": ["stdout"]},
            },
    )

def set_args() -> argparse.ArgumentParser:
    """
    Set the arguments for AutoKeyring.

    Returns:
        argparse.ArgumentParser: The argument parser.
    """
    parser = argparse.ArgumentParser(description="AutoKeyring: Automatically unlock GNOME Keyring with clevis encrypted key.")
    parser.add_argument(
        "--initial-setup",
        action="store_true",
        required=False,
        help="Run the initial setup of the application. This will generate a new key and keyring.",
    )
    parser.add_argument(
        "-k",
        "--generate-key",
        action="store_true",
        required=False,
        help="Generate a new key for unlocking the keyring. To also generate a new keyring, use --initial-setup.",
    )
    parser.add_argument(
        "-r",
        "--generate-keyring",
        action="store_true",
        help="Generate a new keyring using an existing key. To also generate a new key, use --initial-setup.",
    )
    parser.add_argument('-a', '--alias', type=str, default='Login', help='The keyring alias to use. Defaults to "Login".')
    return parser

def wait_for_valid_session(sleep_time: int | None = None) -> "LogindSession | None":
    """
    Waits for a valid session to be available. This function loops indefinitely until a valid session is found.

    Args:
        sleep_time (int): The time to sleep between each check for a valid session.

    Returns:
        LogindSession | None: The valid LogindSession object if found, or None if no valid session is available.
    """
    sleep_time = sleep_time or 60
    while True:
        s = LogindSession.get_active_session()
        if s and s.is_valid_session():
            return s
        time.sleep(sleep_time)

def handle_file_operations(file_path: Path, write_content: bytes, file_description: str = 'file', modhex = 0o400) -> None:
    """
    Handles file operations such as creation, writing, and permission setting for a specified file.

    Args:
        file_path (Path): The path to the file to be operated on.
        write_content (bytes): The content to write to the file.
        file_description (str, optional): A description of the file. Defaults to 'file'.
        modhex (optional): The permission mode to set for the file. Defaults to 0o400.

    Returns:
        None

    Raises:
        ValueError: If the operation fails to create or modify the file.
    """

    if file_path.exists() and file_path.stat().st_size > 0:
        os.rename(file_path, file_path.with_suffix(".old"))
    file_path.touch()
    file_path.write_bytes(write_content)
    if file_path.stat().st_size > 0:
        file_path.chmod(modhex)
        print(f"A new {file_description} was created at {str(file_path)}")
    else:
        file_path.unlink(missing_ok=True)
        raise ValueError(f"Failed to create a new {file_description}")

def get_xdg_dirs() -> tuple[Path, Path]:
    """
    Get the XDG directories.

    Returns:
        tuple[str, str]: The XDG directories.
    """
    xdg_data_home = Path(os.getenv("XDG_DATA_HOME", "~/.local/share"))
    xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", "~/.config"))
    return xdg_data_home.expanduser(), xdg_config_home.expanduser()

class LogindSession:
    """
    Represents a logind session.
    """
    def __init__(self, session_dict) -> None:
        """
        Initializes a LogindSession object with the provided session dictionary.
        *Note*: You should use the `from_logins` or `get_active_session` classmethods to create a LogindSession object.

        Raises:
            AttributeError: If the 'uid' attribute is missing or invalid.
        """

        for key, value in session_dict.items():
            setattr(self, key, value)

    @classmethod
    def get_active_session(cls) -> "LogindSession | None":
        """
        Gets the active logind session. This method searches for the active session and returns the LogindSession object if found.

        Returns:
            LogindSession | None: The active LogindSession object if found, or None if no active session is found.
        """
        sessions = cls.from_logins()
        return next(
            (session for session in sessions if session.is_valid_session()), None
        )



    @classmethod
    def parse_sessions_variants(cls, sessions_variant: Variant) -> list["LogindSession"]:
        """
        Parses session variants to create a list of LogindSession objects.

        Args:
            sessions_variant (Variant): The variant containing session information.

        Returns:
            list["LogindSession"]: A list of LogindSession objects parsed from the sessions variant.
        """

        session_dicts = []
        for session in sessions_variant.unpack()[0]:
            session_id, user_id, user_name, seat_id, object_path = session
            session_info: Variant = bus.call_sync(
                'org.freedesktop.login1',
                object_path,
                'org.freedesktop.DBus.Properties',
                'GetAll',
                GLib.Variant('(s)', ('org.freedesktop.login1.Session',)),
                GLib.VariantType('(a{sv})'),
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )

            properties = {
                k: v.unpack() if isinstance(v, GLib.Variant) else v
                for k, v in session_info.unpack()[0].items()
            } | {
                'session_id': session_id,
                'uid': user_id,
                'user_name': user_name,
                'seat_id': seat_id,
            }
            session_dicts.append(cls(properties))

        return session_dicts

    @classmethod
    def from_logins(cls) -> list["LogindSession"]:
        """
        Creates a list of LogindSession objects from login sessions.

        Returns:
            list["LogindSession"]: A list of LogindSession objects parsed from the login sessions.
        """

        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

        return cls.parse_sessions_variants(bus.call_sync(
            'org.freedesktop.login1',
            '/org/freedesktop/login1',
            'org.freedesktop.login1.Manager',
            'ListSessions',
            None,
            GLib.VariantType('(a(susso))'),
            Gio.DBusCallFlags.NONE,
            -1,
            None
        ))

    def __repr__(self) -> str:
        """
        Returns a string representation of the LogindSession object with session details.

        Returns:
            str: A string representation of the LogindSession object.
        """

        return f"LogindSession(session_id={self.session_id}, uid={self.uid}, user_name={self.user_name}, seat_id={self.seat_id})"

    def is_valid_session(self) -> bool:
        return getattr(self, 'uid', None) is not None and 1000 <= self.uid < 65534

@define
class TPM:
    tpm_available: bool = field(default=False, init=False)

    def __attrs_post_init__(self) -> None:
        self.tpm_available = self.check_for_tpm()
        if self.tpm_available:
            logger.info("TPM device found")

        return None


    @staticmethod
    def check_for_tpm() -> bool:
        """
        Checks if a TPM device is available.

        Returns:
            bool: True if a TPM device is available, False otherwise.
        """
        base_path = Path('/dev')
        return base_path.glob('tpm?') or base_path.glob('tpmrm?')

class TPMStore:

    def __init__(self) ->
