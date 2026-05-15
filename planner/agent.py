from google.adk.agents.llm_agent import Agent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.sequential_agent import SequentialAgent
from .prompt import WORKFLOW_PLANNER_AGENT_PROMPT, REVIEWER_AGENT_PROMPT, REFINER_WORKFLOW_AGENT_PROMPT, REVIEWER_DYNAMIC_PROMPT, REFINER_WORKFLOW_DYNAMIC_PROMPT
from .tools import get_actions_operators, exit_evaluation_loop

model = LiteLlm(
    model='openai/gpt-4o',
)

innitial_workflow_planner_agent = Agent(
    model=model,
    name='innitial_workflow_planner_agent',
    description='A workflow planner agent for the user to create a workflow to perform a task.',
    static_instruction=WORKFLOW_PLANNER_AGENT_PROMPT,
    tools=[get_actions_operators],
    output_key="proposed_workflow",
)

reviewer_agent = Agent(
    model=model,
    name="reviewer_agent",
    description="A workflow reviewer agent to audit the proposed plan by the parent agent",
    static_instruction=REVIEWER_AGENT_PROMPT,
    instruction=REVIEWER_DYNAMIC_PROMPT,
    output_key="evaluation_state",
)

refiner_workflow_agent = Agent(
    model=model,
    name="refiner_workflow_agent",
    description="A workflow refiner agent to refine the proposed workflow by the user.",
    static_instruction=REFINER_WORKFLOW_AGENT_PROMPT,
    instruction=REFINER_WORKFLOW_DYNAMIC_PROMPT,
    tools=[get_actions_operators, exit_evaluation_loop],
)

eveluation_loop_agent = LoopAgent(
    name="eveluation_loop_agent",
    description="A loop agent to evaluate the proposed workflow and create a new one if needed",
    sub_agents=[reviewer_agent, refiner_workflow_agent],
    max_iterations=5,
)

workflow_creator_agent=SequentialAgent(
    name="workflow_creator_agent",
    description="A workflow creator agent to create a new workflow for the user.",
    sub_agents=[
        innitial_workflow_planner_agent, 
        eveluation_loop_agent
    ],
)

root_agent = Agent(
    model=model,
    name="root_agent",
    description="A root agent to evaluate the proposed workflow and create a new one if needed",
    instruction="""
    You are a root agent to evaluate the proposed workflow of the user or create and evaluate a new workflow.

    ## Sub-Agents
    - `workflow_creator_agent`: A workflow creator agent to create, evaluate and refine a new workflow.

    """,
    sub_agents=[workflow_creator_agent],
)
