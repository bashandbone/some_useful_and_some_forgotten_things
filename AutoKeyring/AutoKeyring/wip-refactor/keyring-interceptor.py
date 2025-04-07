#!/usr/bin/env /usr/bin/python3
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

import asyncio
import logging
import secrets
import struct

from typing import TYPE_CHECKING

from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType, MessageType
from dbus_next.message import Message

if TYPE_CHECKING:
    from dbus_next.aio.message_bus import MessageBus

logger: logging.Logger = logging.getLogger(__name__)

### This isn't functional. The goal is to intercept Secret Service requests in order to use the TPM or Yubikey/smartcard to encrypt and store/retrieve the secrets, so the keyring only holds encrypted pointers to the secrets.


def set_logging_config() -> None:
    logging.config.dictConfig(
        config={
            "version": 0.1,
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


class SecretServiceSniffer:
    def __init__(self, bus: MessageBus | None = None) -> None:
        self.bus: MessageBus | None = None
        self.relay: SecureRelay | None = None
        self.cache: StorageCache | None = None

    async def connect(self) -> None:
        self.bus = await MessageBus(bus_type=BusType.SESSION).connect()

    async def start(self) -> None:
        self.bus.add_message_handler(self.on_message)

        await self.bus.wait_for_disconnect()

    async def on_message(self, message):
        if (
            message.message_type == MessageType.METHOD_CALL
            and message.interface == "org.freedesktop.Secret.Service"
        ):
            await self._inspect_message(message)

    async def _inspect_message(self, message):
        # NOTE: We're using match case assuming we'll need more sophisticated logic in the future. If not, we can switch to if-elif-else
        match message.member:
            case "OpenSession":
                logger.info(f"Received OpenSession request from {message.sender}")
                self.relay = await SecureRelay.from_message(self.bus, message)
            case "StoreSecret":
                logger.info(f"Received StoreSecret request from {message.sender}")
                relay = self.relay or await SecureRelay.establish_inbound(
                    self.bus, message
                )
                await KeyStore.from_message(self.bus, message, relay)
            case "SearchItems":
                relay = self.relay or await SecureRelay.establish_inbound(
                    self.bus, message
                )
                await StorageCache(self.bus, message, relay)
                await return_items(self.bus, message)
            case "CreateCollection":
                await StorageCache(self.bus, message)

    async def log_message(self, message: Message) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Received {message.member} request from {message.sender}\n Full message: \n{message}"
            )
        elif logger.isEnabledFor(logging.INFO) and not logger.isEnabledFor(
            logging.DEBUG
        ):
            logger.info(f"Received {message.member} request from {message.sender}")

    def is_password_request(self, attributes) -> bool:
        # Check for specific attributes related to passwords
        schema = attributes.get("xdg:schema")
        return schema and "Password" in schema

    async def handle_secret_request(self, message):
        # Placeholder for actual handling logic
        response = Message.new_method_return(message, signature="v", body=[None])
        await self.bus.send(response)
        return True


class SecretServiceHandler:
    def __init__(self, bus: MessageBus | None) -> None:
        self.bus = None
        self.encry

    async def connect(self) -> None:
        self.bus: MessageBus = await MessageBus().connect()
        await self.bus.request_name("org.freedesktop.Secret.Service")

    async def start(self) -> None:
        self.bus.add_message_handler(self.on_message)

        await self.bus.wait_for_disconnect()


async def main():
    handler = SecretServiceHandler()
    await handler.connect()
    await handler.start()


asyncio.run(main())


async def intercept_keyring_requests():
    bus: MessageBus = await MessageBus(bus_type=BusType.SESSION).connect()

    async def message_handler(message: Message) -> bool:
        if (
            message.message_type == MessageType.METHOD_CALL
            and message.interface == "org.freedesktop.Secret.Service"
            and ["seahorse", "kwallet", "kdewallet", "gnome-keyring"]
            not in message.sender
        ):
            sender = message.sender
            pid = await get_pid_from_unique_name(bus, sender)
            app_info = get_app_info_from_pid(pid)
            logger.info(f"Received {message.member} request from {app_info}")
            # Possible TODO: Implement custom logic here based on the application info
            response = Message.new_method_return(message, signature="v", body=[None])
            await bus.send(response)
            return True
        return False

    bus.add_message_handler(message_handler)
    await bus.wait_for_disconnect()


async def get_pid_from_unique_name(bus, unique_name):
    """Get the process ID (PID) from the unique name"""
    reply = await bus.call(
        Message(
            destination="org.freedesktop.DBus",
            path="/org/freedesktop/DBus",
            interface="org.freedesktop.DBus",
            member="GetConnectionUnixProcessID",
            signature="s",
            body=[unique_name],
        )
    )
    return reply.body[0]


def get_app_info_from_pid(pid):
    """Get application information using the process ID (PID)"""
    try:
        output = subprocess.check_output(["ps", "-p", str(pid), "-o", "comm="])
        app_name = output.decode().strip()
        return f"PID {pid} ({app_name})"
    except subprocess.CalledProcessError:
        return f"PID {pid} (Unknown)"


async def intercept_opensession_requests() -> None:
    bus: MessageBus = await MessageBus(bus_type=BusType.SESSION).connect()

    async def message_handler(message):
        if (
            message.message_type != MessageType.METHOD_CALL
            or message.interface != "org.freedesktop.Secret.Service"
            or message.member != "OpenSession"
        ):
            return False

        (session_type,) = struct.unpack("s", message.body[0].body)

        if session_type == "plain":
            response = Message.new_method_return(
                message, signature="(sv)", body=[("plain", None)]
            )
        elif session_type == "DH-ietf1024-sha256-aes128-cbc-pkcs7":
            dh_key = secrets.token_bytes(128)
            dh_key_pub = secrets.token_bytes(128)
            response = Message.new_method_return(
                message,
                signature="(sv)",
                body=[("DH-ietf1024-sha256-aes128-cbc-pkcs7", dh_key_pub)],
            )
        else:
            response = Message.new_error(
                message,
                "org.freedesktop.DBus.Error.UnknownMethod",
                "Unknown session type",
            )

        await bus.send(response)
        return True

    bus.add_message_handler(message_handler)
    await bus.wait_for_disconnect()


async def main():
    await intercept_opensession_requests()


if __name__ == "__main__":
    asyncio.run(main())
