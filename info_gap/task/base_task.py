"""Module for base class."""

from typing import Iterable


class BaseTask:
    """Base class for all tasks."""

    def get_name(self) -> str:
        """Get the name of the task."""
        raise NotImplementedError

    def get_priority(self) -> int:
        """Get the priority of the task."""
        raise NotImplementedError

    def run(self) -> Iterable["BaseTask"]:
        """Run the task, return subtasks it generates."""
        raise NotImplementedError
