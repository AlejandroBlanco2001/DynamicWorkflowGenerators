from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

model = LiteLlm(
    model='openai/gpt-4o',
)

root_agent = Agent(
    model=model,
    name='executor_agent',
    description='A executor agent to execute the workflow.',
    instruction='You are a executor agent to execute the workflow.',
)
