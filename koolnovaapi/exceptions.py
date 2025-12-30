"""Exceptions for Flipr."""

from typing import Any


class KoolnovaError(Exception):
    """Error from Flipr api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception.

        Args:
            args: the message or root cause of the error
        """
        Exception.__init__(self, *args)
