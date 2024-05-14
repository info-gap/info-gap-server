"""Module for base class."""

import logging
from typing import Iterable, List, Optional
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from info_gap.config import LLM_OPENAI, MODEL
from info_gap.task.base_task import BaseTask


class CompletionTask(BaseTask):
    """Base class for all completion tasks."""

    request: str
    history: List[ChatCompletionMessageParam]
    retries: int
    temperature: float

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        priority: int,
        request: str,
        history: Optional[List[ChatCompletionMessageParam]] = None,
        num_retry: int = 2,
        temperature: float = 0,
    ):
        super().__init__(name, priority)
        self.request = request
        self.history = history or []
        self.retries = num_retry
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
            # Run initial completion
            history: List[ChatCompletionMessageParam] = self.history.copy()
            completion = self._complete(history)

            # Retry if failed
            last_exception = None
            for _ in range(self.retries):
                try:
                    # After successful parse, yield result and return
                    result = self.parse_response(completion)
                    yield from result
                    return
                except Exception as e:  # pylint: disable=broad-exception-caught
                    last_exception = e

                    # Upon parse failure, add self-healing message
                    history += [
                        {
                            "role": "assistant",
                            "content": completion,
                        },
                        {
                            "role": "system",
                            "content": str(e),
                        },
                        {
                            "role": "user",
                            "content": self.request,
                        },
                    ]
                    completion = self._complete(history)

            # If all retries failed, raise the last exception
            assert last_exception is not None
            raise last_exception
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
