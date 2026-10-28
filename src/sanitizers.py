"""Sanitizers for Claude Code Anthropic protocol compliance."""
from typing import Dict, Any, List

def sanitize_anthropic_response(result: Dict[str, Any], requested_model: str) -> Dict[str, Any]:
    """Ensures that responses strictly conform to Claude Code expectations."""
    result["model"] = requested_model
    content = result.get("content", [])
    
    # Claude Code requires valid content elements
    has_text = any(b.get("type") == "text" for b in content)
    has_tool = any(b.get("type") == "tool_use" for b in content)
    
    if not has_text and not has_tool:
        # Check if thinking text is present to promote or default to standard text
        thinking_text = "".join(b.get("thinking", "") for b in content if b.get("type") == "thinking")
        if thinking_text and len(thinking_text.strip()) > 0:
            content.append({"type": "text", "text": thinking_text})
        else:
            content.append({"type": "text", "text": "Ready."})
            
    result["content"] = content
    return result
