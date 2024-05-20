"""Entrypoint of program."""

import logging
from examples.coding_agent import REQUEST
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
brainstorm_task = BrainStormTask(request=REQUEST)
scheduler = Scheduler()
scheduler.add_task(brainstorm_task)
scheduler.run()
