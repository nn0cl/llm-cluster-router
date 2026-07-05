When LLM routing is available, inspect the configured providers before
assigning a generation task. For Ollama, use `/api/ps` status to prefer hosts
that already have the requested model loaded in memory, then use `/api/tags` to
confirm local model availability on fallback hosts. For OpenAI, Anthropic, and
Codex SDK providers, confirm that the requested model is configured and that
required credentials or optional SDK dependencies are available. Consider model
suitability, provider health, priority, and recent response metadata. Send only
a compact JSON task package with the system prompt, selected context,
instruction, model, and options. Write generated output directly to the
requested path through the local manager inside the allowed root. Return
metadata only unless the user asks to inspect the generated file.
