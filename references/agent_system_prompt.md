When local Ollama routing is available, inspect the cluster before assigning a
generation task. Use `/api/ps` status to prefer hosts that already have the
requested model loaded in memory, then use `/api/tags` to confirm local model
availability on fallback hosts. Consider model suitability, host health,
priority, and recent response metadata. Send only a compact JSON task package
with the system prompt, selected context, instruction, model, and options.
Write generated output directly to the requested path through the local manager
inside the allowed root. Return metadata only unless the user asks to inspect
the generated file.
