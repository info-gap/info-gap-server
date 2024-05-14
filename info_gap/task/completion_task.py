"""Module for base class."""

import logging
from typing import Iterable, List, Optional
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from info_gap.config import LLM_OPENAI, MODEL
from info_gap.task.base_task import BaseTask


class CompletionTask(BaseTask):
    """Base class for all completion tasks."""

    history: List[ChatCompletionMessageParam]
    temperature: float

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        priority: int,
        temperature: float,
        history: Optional[List[ChatCompletionMessageParam]] = None,
    ):
        super().__init__(name, priority)
        self.history = history or []
        self.temperature = temperature

    def parse_response(self, _: str) -> Iterable["BaseTask"]:
        """Parse the response."""
        raise NotImplementedError

    def after_run(self) -> Iterable["BaseTask"]:
        """Task to run after self is done."""
        yield from []

    def run(self) -> Iterable[BaseTask]:
        """Implemented by running completion. You no longer need to override this method."""
        try:
            history: List[ChatCompletionMessageParam] = self.history.copy()
            completion = self._complete(history)
            result = self.parse_response(completion)
            yield from result
        finally:
            yield from self.after_run()

    def _complete(self, messages: List[ChatCompletionMessageParam]) -> str:
        """Run the completion with given history."""
        logging.debug("REQUEST: %s", messages)
        result = LLM_OPENAI.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=self.temperature,
        )
        logging.debug("RESPONSE: %s", result.choices[0].message.content)
        return result.choices[0].message.content or ""
