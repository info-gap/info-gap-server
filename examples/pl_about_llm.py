"""Example request to find papers about designing a new programming language for LLM model."""

from info_gap.model import Example, Request

# Run application
REQUEST = Request(
    this_paper_should_be="about designing a new programming language for LLM model",
    accepted_reason_format="The name of the programming language is `your_language`. The language is designed for `your_purpose`.",
    unaccepted_reason_format="The paper is not about designing a new programming language for LLM, because `your_reason`.",
    examples=[
        Example(
            title="LLaMA-3: A Large Language Model for Algebraic Reasoning",
            summary="The paper presents LLaMA-3, a large language model for algebraic reasoning.",
            accepted=False,
            reason="The paper is not about designing a new programming language for LLM, because `although it's about LLM, there's no mention of a new programming language`.",
        ),
        Example(
            title="Rust: a memory-safe programming language",
            summary="The paper presents Rust, a memory-safe programming language.",
            accepted=False,
            reason="The paper is not about designing a new programming language for LLM, because `although it's about a programming language, it's not designed for LLM`.",
        ),
        Example(
            title="XEM-Script: Improving the Security of LLM",
            summary="The paper presents XEM-Script, a new programming language that can improve the security of LLM.",
            accepted=True,
            reason="The name of the programming language is `XEM-Script`. The language is designed for `improving the security of LLM.`",
        ),
    ],
)
