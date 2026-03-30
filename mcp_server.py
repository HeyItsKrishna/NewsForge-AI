import asyncio
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import mcp.types as types

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
BASE_URL = "https://newsdata.io/api/1/news"

def fetch_news_from_api(query, max_results=8):
    params = {"apikey": NEWS_API_KEY, "q": query, "language": "en", "size": max_results}
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NewsForgeAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"status": "error", "message": str(e), "results": []}

def fetch_top_headlines(category="technology", max_results=8):
    params = {"apikey": NEWS_API_KEY, "category": category, "language": "en", "size": max_results}
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NewsForgeAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"status": "error", "message": str(e), "results": []}

def format_articles(data):
    if data.get("status") == "error":
        return f"Error: {data.get('message', 'Unknown error')}"
    articles = data.get("results", [])
    if not articles:
        return "No articles found."
    out = []
    for i, a in enumerate(articles[:8], 1):
        title = a.get("title", "No title")
        desc = (a.get("description") or "")[:200]
        source = a.get("source_id", "Unknown")
        date = a.get("pubDate", "Unknown")
        link = a.get("link", "")
        out.append(f"{i}. {title}\n   Source: {source} | {date}\n   {desc}\n   {link}\n")
    return "\n".join(out)

server = Server("newsforge-ai-mcp")

@server.list_tools()
async def handle_list_tools():
    return [
        types.Tool(name="fetch_news", description="Search latest news on any topic.",
            inputSchema={"type":"object","properties":{"query":{"type":"string"},"max_results":{"type":"integer","default":6}},"required":["query"]}),
        types.Tool(name="fetch_top_headlines", description="Top headlines by category.",
            inputSchema={"type":"object","properties":{"category":{"type":"string","enum":["technology","business","science","health","sports","entertainment","politics"],"default":"technology"},"max_results":{"type":"integer","default":6}},"required":[]}),
        types.Tool(name="get_news_summary", description="Structured summary of news on a topic.",
            inputSchema={"type":"object","properties":{"topic":{"type":"string"}},"required":["topic"]})
    ]

@server.call_tool()
async def handle_call_tool(name, arguments):
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    if name == "fetch_news":
        data = fetch_news_from_api(arguments.get("query",""), arguments.get("max_results",6))
        text = f"News for '{arguments.get('query','')}' | {ts}\n\n{format_articles(data)}"
        return [types.TextContent(type="text", text=text)]
    elif name == "fetch_top_headlines":
        cat = arguments.get("category","technology")
        data = fetch_top_headlines(category=cat, max_results=arguments.get("max_results",6))
        text = f"Top Headlines: {cat.upper()} | {ts}\n\n{format_articles(data)}"
        return [types.TextContent(type="text", text=text)]
    elif name == "get_news_summary":
        topic = arguments.get("topic","")
        data = fetch_news_from_api(topic, max_results=10)
        articles = data.get("results",[])
        sources = list(set(a.get("source_id","unknown") for a in articles))
        summary = f"Summary: '{topic}' | {ts}\nTotal: {data.get('totalResults',0)} | Sources: {', '.join(sources[:5])}\n\n"
        for i, a in enumerate(articles[:5],1):
            summary += f"{i}. {a.get('title','No title')}\n"
        return [types.TextContent(type="text", text=summary)]
    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (r, w):
        await server.run(r, w, InitializationOptions(
            server_name="newsforge-ai-mcp", server_version="1.0.0",
            capabilities=server.get_capabilities(notification_options=NotificationOptions(), experimental_capabilities={})))

if __name__ == "__main__":
    asyncio.run(main())
