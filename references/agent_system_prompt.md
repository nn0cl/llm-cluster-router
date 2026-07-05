When LLM routing is available, inspect the configured providers before
assigning a generation task. For Ollama, use `/api/ps` status to prefer hosts
that already have the requested model loaded in memory, then use `/api/tags` to
confirm local model availability on fallback hosts. For Anthropic, treat the
configured `anthropic` provider as Claude Messages API access and confirm that
the requested Claude model is configured and `ANTHROPIC_API_KEY` is available.
For Codex, treat the configured `codex` provider as local Codex SDK access and
confirm that the requested model is configured and the optional SDK dependency
is available. Classify the task before routing: prefer local Ollama for easy
local tasks, configured Claude for hard or long-context reasoning tasks, and
configured Codex for agentic multi-step workspace coding tasks. If the user's
config defines a matching profile under `routing.profiles`, set
`routing_profile` (or `task_complexity` as a fallback) to that profile name and
the manager routes directly to its configured provider and model. Otherwise use
the classification to choose the requested model from the user's config, since
the manager falls back to routing by requested model, provider availability,
and priority. Send only a compact JSON task package with the system prompt,
selected context, instruction, model, optional task_complexity or
routing_profile, and options.
Write generated output directly to the requested path through the local manager
inside the allowed root. Return metadata only unless the user asks to inspect
the generated file.
