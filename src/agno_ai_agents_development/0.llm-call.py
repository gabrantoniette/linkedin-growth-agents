from agno.agent import Agent
from agno.models.anthropic import Claude
from dotenv import load_dotenv
import os
load_dotenv()

anthropic_api_key = os.getenv("CLAUDE_API_KEY")

agent = Agent(
    model=Claude(id="claude-sonnet-4-5-20250929", api_key=anthropic_api_key),
    markdown=True,
)

if __name__ == "__main__":
    agent.print_response("Write a one-sentence horror story.")