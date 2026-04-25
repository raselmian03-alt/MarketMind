import json
import os
import anthropic
from dotenv import load_dotenv

from tools.sales import analyze_sales, TOOL_DEFINITION as SALES_TOOL
from tools.campaign import analyze_campaign, TOOL_DEFINITION as CAMPAIGN_TOOL
from tools.research import research_competitors, TOOL_DEFINITION as RESEARCH_TOOL
from tools.report import generate_report, TOOL_DEFINITION as REPORT_TOOL

load_dotenv()

TOOL_DEFINITIONS = [SALES_TOOL, CAMPAIGN_TOOL, RESEARCH_TOOL, REPORT_TOOL]

TOOL_FUNCTIONS = {
    "analyze_sales": analyze_sales,
    "analyze_campaign": analyze_campaign,
    "research_competitors": research_competitors,
    "generate_report": generate_report,
}

SYSTEM_PROMPT = """You are MarketMind, an expert AI data and marketing analyst agent.

You help users by:
- Analyzing ANY uploaded CSV data — sales, products, cars, surveys, or any dataset
- Evaluating marketing campaign performance (CTR, CPC, CPA, ROAS)
- Researching competitors and market trends
- Generating clear, structured reports

When a message contains a <dataset_analysis> block, it holds pre-computed statistics
(shape, numeric summaries, correlations, categorical breakdowns, sample rows).
Interpret those results directly — do NOT call analyze_sales again.

When a user sends raw csv_data without a pre-computed block:
1. Call analyze_sales with the csv_data
2. Interpret ALL columns — numeric stats, categories, correlations, group insights
3. Highlight interesting patterns, outliers, and relationships
4. Present findings in a clear markdown table or bullet list
5. Offer to generate a formal report if appropriate

Always be concise, data-driven, and specific about numbers."""


def _serialize_content(content) -> list:
    """Convert Anthropic SDK content blocks to plain dicts."""
    if isinstance(content, str):
        return content
    result = []
    for block in content:
        if isinstance(block, dict):
            result.append(block)
        elif hasattr(block, "type"):
            if block.type == "text":
                result.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                result.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
            elif hasattr(block, "model_dump"):
                result.append(block.model_dump())
    return result


def _sanitize_history(messages: list) -> list:
    """
    Remove assistant turns with tool_use that have no matching tool_result
    in the following user message. Also removes the preceding user turn to
    avoid consecutive user messages (which the API also rejects).
    """
    sanitized = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        content = msg.get("content", [])

        if msg.get("role") == "assistant" and isinstance(content, list):
            has_tool_use = any(
                (isinstance(b, dict) and b.get("type") == "tool_use")
                for b in content
            )
            if has_tool_use:
                next_msg = messages[i + 1] if i + 1 < len(messages) else None
                next_content = next_msg.get("content", []) if next_msg else []
                has_result = isinstance(next_content, list) and any(
                    isinstance(b, dict) and b.get("type") == "tool_result"
                    for b in next_content
                )
                if has_result:
                    sanitized.append(msg)
                    sanitized.append(messages[i + 1])
                    i += 2
                    continue
                else:
                    # Drop orphaned tool_use AND its preceding user turn so we
                    # don't end up with two consecutive user messages.
                    if sanitized and sanitized[-1].get("role") == "user":
                        sanitized.pop()
                    i += 1
                    continue

        sanitized.append(msg)
        i += 1

    return sanitized


def _run_loop(client, user_message: str, history: list) -> tuple[str, list]:
    messages = history + [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        serialized = _serialize_content(response.content)
        messages.append({"role": "assistant", "content": serialized})

        if response.stop_reason == "end_turn":
            return _extract_text(response.content), messages

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if hasattr(block, "type") and block.type == "tool_use":
                    result = _call_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            return _extract_text(response.content), messages


def run_agent(
    user_message: str,
    conversation_history: list | None = None,
    api_key: str | None = None,
) -> tuple[str, list]:
    """
    Run the MarketMind agent for one user turn.
    Returns the assistant's final text response and the updated conversation history.
    If the history causes a 400 (tool_use/tool_result mismatch), automatically
    retries with a clean history so the user always gets an answer.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=key)

    clean_history = _sanitize_history(list(conversation_history or []))

    try:
        return _run_loop(client, user_message, clean_history)
    except anthropic.BadRequestError as e:
        err = str(e)
        if "tool_use" in err or "tool_result" in err:
            # History is still corrupt despite sanitization — retry clean.
            return _run_loop(client, user_message, [])
        raise


def _call_tool(name: str, inputs: dict) -> dict:
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return func(**inputs)
    except Exception as e:
        return {"error": str(e)}


def _extract_text(content) -> str:
    return "\n".join(
        block.text for block in content if hasattr(block, "text")
    ).strip()
