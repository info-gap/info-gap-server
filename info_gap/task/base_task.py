"""Module for base class."""

from typing import Iterable


class BaseTask:
    """Base class for all tasks."""

    name: str
    priority: int

    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority

    def run(self) -> Iterable["BaseTask"]:
        """Run the task, return subtasks it generates."""
        raise NotImplementedError
