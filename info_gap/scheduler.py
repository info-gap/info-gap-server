"""Scheduler of tasks."""

from typing import List
from openai import BadRequestError
from instructor.retry import InstructorRetryException  # type: ignore
from info_gap.task.base_task import BaseTask


class Scheduler:
    """Scheduler of tasks."""

    tasks: List[BaseTask]

    def __init__(self):
        self.tasks = []

    def add_task(self, task: BaseTask):
        """Add a task to the scheduler."""
        self.tasks.append(task)

    def run(self):
        """Run the scheduler."""
        while self.tasks:
            self.tasks.sort(key=lambda task: task.get_priority(), reverse=True)
            task = self.tasks.pop(0)
            try:
                print(f'🔥 Running task "{task.get_name()}" [{task.get_priority()}]')
                subtasks = task.run()
                for subtask in subtasks:
                    self.add_task(subtask)
            except BadRequestError as e:
                print(f'😭 Server is unstable: "{e}", aborting!')
            except InstructorRetryException as e:
                print(f'😭 Max retry exceeded: "{e}", aborting!')
            except ConnectionError as e:
                print(f'😭 Connection is unstable: "{e}", aborting!')
