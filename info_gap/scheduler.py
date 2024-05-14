"""Scheduler of tasks."""

import logging
from typing import List
from info_gap.task.base_task import BaseTask


class Scheduler:
    """Scheduler of tasks."""

    tasks: List[BaseTask]
    error_counter: int

    def __init__(self):
        self.tasks = []
        self.error_counter = 0

    def add_task(self, task: BaseTask):
        """Add a task to the scheduler."""
        self.tasks.append(task)

    def run(self):
        """Run the scheduler."""
        while self.tasks:
            self.tasks.sort(key=lambda task: task.priority, reverse=True)
            task = self.tasks.pop(0)
            try:
                print(f'🔥 Running task "{task.name}" [{task.priority}]')
                subtasks = task.run()
                for subtask in subtasks:
                    self.add_task(subtask)
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.error_counter += 1
                error_msg = f'😭 Error #{self.error_counter}: "{e}", aborting!'
                print(error_msg)
                logging.debug(error_msg)
