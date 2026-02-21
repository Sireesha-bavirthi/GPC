"""
APO v2 — LLM Router
====================
Tries Claude first → falls back to GPT-4o → falls back to rules.
All agents call this module instead of hitting APIs directly.
"""

import json
from core.config import (
    ANTHROPIC_API_KEY, OPENAI_API_KEY,
    CLAUDE_MODEL, OPENAI_MODEL
)

_anthropic_ok = bool(ANTHROPIC_API_KEY)
_openai_ok    = bool(OPENAI_API_KEY)


def call_llm(prompt: str, tools: list = None,
             system: str = "", max_tokens: int = 1024) -> dict:
    """
    Universal LLM caller.
    Returns {"provider": str, "tool_result": dict | None, "text": str}

    Priority: Claude → GPT-4o → None (caller uses rule fallback)
    """
    # ── Try Claude ─────────────────────────────────────────────
    if _anthropic_ok:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            kwargs = dict(
                model=CLAUDE_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            if system:
                kwargs["system"] = system
            if tools:
                kwargs["tools"] = tools

            resp = client.messages.create(**kwargs)

            # Extract tool_use block if present
            for block in resp.content:
                if block.type == "tool_use":
                    return {
                        "provider":    "claude",
                        "tool_result": block.input,
                        "text":        ""
                    }
            # Plain text response
            return {
                "provider":    "claude",
                "tool_result": None,
                "text":        resp.content[0].text if resp.content else ""
            }
        except Exception as e:
            print(f"  [LLM] Claude failed ({type(e).__name__}), trying GPT-4o...")

    # ── Try GPT-4o ─────────────────────────────────────────────
    if _openai_ok:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Convert Anthropic-style tools to OpenAI format if provided
            oai_tools = None
            if tools:
                oai_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name":        t["name"],
                            "description": t["description"],
                            "parameters":  t["input_schema"],
                        }
                    }
                    for t in tools
                ]

            kwargs = dict(model=OPENAI_MODEL, messages=messages, max_tokens=max_tokens)
            if oai_tools:
                kwargs["tools"]       = oai_tools
                kwargs["tool_choice"] = "required"

            resp = client.chat.completions.create(**kwargs)
            choice = resp.choices[0]

            # Tool call result
            if choice.message.tool_calls:
                tc = choice.message.tool_calls[0]
                return {
                    "provider":    "gpt4o",
                    "tool_result": json.loads(tc.function.arguments),
                    "text":        ""
                }
            return {
                "provider":    "gpt4o",
                "tool_result": None,
                "text":        choice.message.content or ""
            }
        except Exception as e:
            print(f"  [LLM] GPT-4o failed ({type(e).__name__}): {e}")

    # ── No LLM available ───────────────────────────────────────
    return {"provider": "none", "tool_result": None, "text": ""}
