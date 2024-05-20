"""Example request to find papers about coding agent."""

from info_gap.model import Example, Request

# Run application
REQUEST = Request(
    this_paper_should_be="about automatic software development with large language models and multi-agent",
    accepted_reason_format="The exhaustive list of agents is `your_agents`. The agents communicate by `your_method`. The agents are designed for `your_purpose`.",
    unaccepted_reason_format="The paper is not about automatic software development with large language models and multi-agent, because `your_reason`.",
    examples=[
        Example(
            title="LLaMA-3: A Large Language Model for Algebraic Reasoning",
            summary="The paper presents LLaMA-3, a large language model for algebraic reasoning.",
            accepted=False,
            reason="The paper is not about automatic software development with large language models and multi-agent, because `although it's about LLM, there's no mention of multi-agent`.",
        ),
        Example(
            title="DeepSeekCode: A code-generation model for software development",
            summary="The paper presents DeepSeekCode, a code-generation model for software development.",
            accepted=False,
            reason="The paper is not about automatic software development with large language models and multi-agent, because `although it's about software development with LLM, there's no mention of multi-agent`.",
        ),
        Example(
            title="OmniAgent: A multi-agent system for automatic software development",
            summary="The paper presents OmniAgent, a multi-agent system for automatic software development. TWe propose a message-pool architecture for agents to communicate with each other. Agents include Product Manager, Developer, Tester, and Deployer. The agents are designed for improving the efficiency of software development.",
            accepted=True,
            reason="The exhaustive list of agents is `Product Manager, Developer, Tester, and Deployer`. The agents communicate by `message-pool architecture`. The agents are designed for `improving the efficiency of software development`.",
        ),
    ],
)
