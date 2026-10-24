# LLM Chat integration

ID: `backend.integration.llm_chat`
Category: `backend`

Make raw OpenAI-compatible Chat Completions calls through Hangar, with caller-configured tools and request options.

## Import

`from hangarkit.integrations import llm_chat`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `llm_chat.chat_completions.create(messages, model=None, timeout=120, tools=None, tool_choice=None, parallel_tool_calls=None, response_format=None, **request_options)`

## Details

Use `llm_chat` when app code needs the raw OpenAI Chat Completions contract rather than a managed Wingman agent. `chat_completions.create()` forwards standard non-streaming Chat Completions request fields to Hangar's OpenAI-compatible provider and returns the provider response unchanged. `model` defaults to the Hangar LLM model when omitted. Pass tool definitions through `tools=[...]`; pass `tool_choice="auto"`, `tool_choice="required"`, or a named function choice when you need to control selection.

The caller owns the entire interaction: provide the full `messages` history on every request; define `tools`, `tool_choice`, `parallel_tool_calls`, `response_format`, sampling controls, and other provider-supported request options; execute any returned tool calls; then append the assistant tool-call message and your `role="tool"` results before calling again. Hangar does not persist a session or execute tools for this integration. `stream=True` is not supported by this helper.

This is intentionally unlike `wingman_chat`: there are no built-in Wingman or Toolverse tools, no automatic agent behavior, and no normalized `content` response. It is available only when Hangar is configured with an OpenAI-compatible LLM provider. Every request is audited and counts against `settings.integrations.llm_chat.monthly_cost_quota` when configured.

```python
import json
from hangarkit.integrations import llm_chat

messages = [{"role": "user", "content": "What is the status of order 42?"}]
tools = [{
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "Look up one order by its ID.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
    },
}]

completion = llm_chat.chat_completions.create(
    messages=messages,
    tools=tools,
    tool_choice="auto",
)
assistant_message = completion["choices"][0]["message"]

# The app, not Hangar, executes the requested function.
tool_call = assistant_message["tool_calls"][0]
arguments = json.loads(tool_call["function"]["arguments"])
tool_result = get_order_status(arguments["order_id"])

# Send the tool result back as the next OpenAI-compatible turn.
messages.extend([
    assistant_message,
    {
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": json.dumps(tool_result),
    },
])
final_completion = llm_chat.chat_completions.create(messages=messages, tools=tools)
answer = final_completion["choices"][0]["message"]["content"]
```

This is a backend runtime helper injected by Hangar. It is not a local Python package in a plain dev environment.
## Quick examples

- `completion = llm_chat.chat_completions.create(messages=[{"role": "user", "content": "Draft a reply"}])`
- `completion = llm_chat.chat_completions.create(messages=messages, tools=tools, tool_choice="auto")`

## Related capabilities

- `backend.integrations`
- `backend.integration.wingman_chat`
