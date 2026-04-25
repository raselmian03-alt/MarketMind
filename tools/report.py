from datetime import datetime


def generate_report(
    title: str,
    sections: list[dict],
    format: str = "markdown",
) -> dict:
    """Assemble a structured marketing report from provided sections."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    if format == "markdown":
        lines = [f"# {title}", f"*Generated: {timestamp}*", ""]
        for section in sections:
            heading = section.get("heading", "Section")
            content = section.get("content", "")
            lines.append(f"## {heading}")
            lines.append(content)
            lines.append("")
        report_text = "\n".join(lines)
    else:
        report_text = f"{title}\nGenerated: {timestamp}\n\n"
        for section in sections:
            heading = section.get("heading", "Section")
            content = section.get("content", "")
            report_text += f"{heading}\n{'-' * len(heading)}\n{content}\n\n"

    return {
        "title": title,
        "format": format,
        "generated_at": timestamp,
        "report": report_text,
        "section_count": len(sections),
    }


TOOL_DEFINITION = {
    "name": "generate_report",
    "description": (
        "Assemble a structured marketing report in Markdown or plain text. "
        "Accepts a title and a list of sections (each with a heading and content). "
        "Use this to produce a final deliverable for the user."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Report title.",
            },
            "sections": {
                "type": "array",
                "description": "List of report sections.",
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["heading", "content"],
                },
            },
            "format": {
                "type": "string",
                "enum": ["markdown", "plain"],
                "description": "Output format: 'markdown' (default) or 'plain'.",
                "default": "markdown",
            },
        },
        "required": ["title", "sections"],
    },
}
