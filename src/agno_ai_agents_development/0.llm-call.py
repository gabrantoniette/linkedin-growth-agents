from agno.agent import Agent
from agno.models.anthropic import Claude
from dotenv import load_dotenv
import os
load_dotenv()

anthropic_api_key = os.getenv("CLAUDE_API_KEY")

agent = Agent(
    model=Claude(id="claude-sonnet-5", 
        api_key=anthropic_api_key,
        effort="medium",
        max_tokens=1000000
    )
)

if __name__ == "__main__":
    agent.print_response("Write a one-sentence horror story.")