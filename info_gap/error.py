"""Errors that will be raised in tasks."""


class ValidationError(Exception):
    """Error raised when a validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
