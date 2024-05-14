"""Entrypoint of program."""

import logging
from info_gap.task.brainstorm import BrainStormTask
from info_gap.scheduler import Scheduler
from info_gap.config import LOG_PATH

# Redirect debug log to file
logging.basicConfig(
    filename=f"{LOG_PATH}/debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Run application
REQUEST = "Can you find me some papers about designing a new programming language for LLM model?"
brainstorm_task = BrainStormTask(request=REQUEST)
scheduler = Scheduler()
scheduler.add_task(brainstorm_task)
scheduler.run()
