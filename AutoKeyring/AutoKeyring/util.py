import ctypes
import contextlib

    @staticmethod
    def zeroize(secret: bytearray | bytes) -> None:
        """
        Zeroizes the provided secret by converting it to a ctypes array, identifying the memory pointer, and setting each bit to zero.

        Args:
            secret (bytearray | bytes): The secret to zeroize.

        Returns:
            None
        """
        buffer = (ctypes.c_char * len(secret)).from_buffer(secret)
        ctypes.memset(buffer, 0, len(secret))
        del buffer # totally unnecessary, but ... paranoia.
