import os
import time
import json
from openai import OpenAI

import tools as tools

# ---------------------------------------------------------------------------
# Initialize OpenAI client pointed at OpenRouter
# Using the OpenAI SDK with OpenRouter's base URL is the recommended approach
# for accessing OpenRouter-specific parameters (e.g. include_reasoning) via
# extra_body, which the native OpenRouter SDK does not yet support.
# See: https://github.com/openai/openai-python
#      https://openrouter.ai (OpenAI-compatible API)
# ---------------------------------------------------------------------------

# If Environment variables fail I WANT IT TO CRASH so I know the problem is with this
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = os.environ["LLM_BASE_URL"]
LLM_MODEL = os.environ["LLM_MODEL"]
CONTEXT_WINDOW = int(os.environ["CONTEXT_WINDOW"])
HALLUNCINATION_THRESHOLD = 0.75
GIT_USER_NAME = os.environ["GIT_USER_NAME"]
GIT_USER_EMAIL = os.environ["GIT_USER_EMAIL"]
WORKING_DIR = os.environ["WORKING_DIR"]

client = OpenAI(
    api_key = LLM_API_KEY,
    base_url = LLM_BASE_URL,
    default_headers={
        "X-OpenRouter-Title": "BookWorm Engineer"
    }
)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    system_prompt = f"""
You are an advanced agent working inside a structured Harness Engineering pipeline.
The repository state serves as your absolute system of record.
Your Working Directory is {WORKING_DIR}. The tools "read_file", "write_file" and "bash" all use in this directory.

Initialize git config with these commands:
> git config --global user.name "{GIT_USER_NAME}"
> git config --global user.email "{GIT_USER_EMAIL}"

You must initialize the correct environment for the project (e.g. venv). This is to ensure dependencies are installed correctly (i.e. "pip install ...").

Once a feature is completed you must do these before trying to implement the next feature
> Append to and clean up PROGRESS.md with tool updates.
> Commit all changes to the local git repository with an appropriate message using the 'bash' tool.
  > No need to push to remote.
  > IMPORTANT: Always stage changes of PROGRESS.md BEFORE commiting to git. By the final git commit, all changes of PROGRESS.md must be included.

### HIGH-LEVEL DIRECTORY RULES (AGENTS.md)\n
{tools.read_file(os.path.join(WORKING_DIR, "AGENTS.md"))}

### RUNTIME CONTINUITY STATE (PROGRESS.md)
{tools.read_file(os.path.join(WORKING_DIR, "PROGRESS.md"))}

OPERATING MANDATE:
1. Review user tasks alongside the rigid guardrails outlined in AGENTS.md.
2. If building files, you MUST run verification commands listed under AGENTS.md via the 'bash' tool to ensure compliance.
3. Prior to concluding your processing loop you must remember to update PROGRESS.md and commit changes to Git again.
"""
    print(system_prompt, end="\n\n")

    print("================= User Prompt ===============================", end="\n\n")
    user_prompt = input("> ").strip()
    print("")
    print("================= Agent Output ===============================", end="\n\n")
    start_time = time.time()

    messages: list = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]

    try:
        # Agentic loop: keep going until the model stops calling tools.
        # extra_body passes OpenRouter-specific parameters not in the OpenAI spec.
        # include_reasoning exposes the model's reasoning tokens in reply.reasoning.
        # See: https://openrouter.ai/docs/guides/best-practices/reasoning-tokens
        while True:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=tools.schema,
                extra_body={
                    "reasoning": {
                        "effort": "low"  # Maps to thinkingLevel: "low"
                    }
                },
            )

            # OpenAI SDK response schema: response.choices[0].message
            reply = response.choices[0].message
            # getattr(reply, "reasoning", None)

            if reply.reasoning: # pyright: ignore[reportAttributeAccessIssue]
                print("Thinking: ", reply.reasoning, end="\n\n") # pyright: ignore[reportAttributeAccessIssue]
            print("Content: ", reply.content, end="\n\n")

            # Append assistant turn to history as a plain dict
            messages.append({
                "role":       "assistant",
                "content":    reply.content or "",
                "tool_calls": [
                    {
                        "id":   tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name, # pyright: ignore[reportAttributeAccessIssue]
                            "arguments": tc.function.arguments # pyright: ignore[reportAttributeAccessIssue]
                        }
                    }
                    for tc in (reply.tool_calls or [])
                ] or None
            })

            tool_calls = reply.tool_calls or []

            if not tool_calls:
                # No more tool calls — print the final reply and exit
                elapsed = time.time() - start_time
                hours, rem = divmod(elapsed, 3600)
                minutes, seconds = divmod(rem, 60)
                print(f"Time taken: {int(hours):02}:{int(minutes):02}:{seconds:05.2f}", end="\n\n")
                break

            # Execute each tool call and feed results back
            for tc in tool_calls:
                fn_name = tc.function.name # pyright: ignore[reportAttributeAccessIssue]
                # arguments may be a dict already or a JSON string depending on the model
                fn_args = tc.function.arguments # pyright: ignore[reportAttributeAccessIssue]
                if isinstance(fn_args, str):
                    fn_args = json.loads(fn_args)

                msg = f"Calling {fn_name} with arguments {fn_args}"
                print(msg if len(msg) <= 200 else msg[:200] + "… … …", end="\n\n")

                if fn_name in tools.available_functions:
                    try:
                        result = tools.available_functions[fn_name](**fn_args)
                    except TypeError as e:
                        result = (
                            f"Error calling {fn_name}: {e}. "
                            "Tool calling must specify all arguments by name\n"
                        )
                else:
                    result = f"Unknown tool: {fn_name}"

                print(f"Result: {result}", end="\n\n")

                # Tool result message — role must be "tool" with matching tool_call_id
                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      str(result)
                })
            
                # HALLUNCINATION THRESHOLD tell the LLM to wrap up if Context Window fills beyond this threshold
                if response.usage is not None:
                    context_used = response.usage.prompt_tokens / CONTEXT_WINDOW
                    if context_used >= HALLUNCINATION_THRESHOLD:
                        messages.append({
                            "role": "system",
                            "content": f"WARNING: {context_used} of context window used. "
                                        "You MUST conclude this processing loop as soon as possible.\n"
                        })
                        print(f"[WARNING]: {context_used} of context window used. Threshold is {HALLUNCINATION_THRESHOLD}.")
                        break

    except Exception as e:
        raise RuntimeError(f"Failed to generate response: {e}") from e