import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

AGENT_INSTRUCTION = """
You are NewsForge AI, an intelligent news analysis agent with access to live news data through MCP tools.

When a user asks about news or current events:
1. Use fetch_news to retrieve latest headlines on their topic
2. Analyze and summarize key findings
3. Identify trends, sentiment, and important takeaways
4. Present insights clearly with these sections:
   - HEADLINES
   - KEY INSIGHTS
   - SENTIMENT (Positive/Neutral/Negative)
   - WHAT THIS MEANS

Always be concise, insightful, and helpful.
"""

def create_agent():
    mcp_toolset = MCPToolset(
        connection_params=StdioServerParameters(
            command="python",
            args=["mcp_server.py"],
            env={
                "NEWS_API_KEY": os.environ.get("NEWS_API_KEY", ""),
                "PYTHONPATH": ".",
            }
        )
    )
    agent = LlmAgent(
        name="newsforge_ai",
        model=os.environ.get("MODEL", "gemini-2.5-flash-preview-04-17"),
        instruction=AGENT_INSTRUCTION,
        tools=[mcp_toolset],
        description="NewsForge AI — intelligent news analysis agent powered by Google ADK and MCP."
    )
    return agent

root_agent = create_agent()
