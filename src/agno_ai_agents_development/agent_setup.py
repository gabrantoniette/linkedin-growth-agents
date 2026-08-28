from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.websearch import WebSearchTools
from dotenv import load_dotenv
import os
load_dotenv()

anthropic_api_key = os.getenv("CLAUDE_API_KEY")

agent = Agent(
    model=Claude(
        id="claude-sonnet-5", 
        effort="medium",
        api_key=anthropic_api_key,
        tools=[WebSearchTools()]
    )
)