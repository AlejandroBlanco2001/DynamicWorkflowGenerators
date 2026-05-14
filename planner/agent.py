from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompt import WORKFLOW_PLANNER_AGENT_PROMPT
from .tools import get_actions_operators

model = LiteLlm(
    model='openai/gpt-4o',
)

root_agent = Agent(
    model=model,
    name='root_agent',
    description='A workflow planner agent for the user to create a workflow to perform a task.',
    instruction=WORKFLOW_PLANNER_AGENT_PROMPT,
    tools=[get_actions_operators],
)
