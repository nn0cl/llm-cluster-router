# Work Plan: Fallback-Based LLM Routing

## Status

Cancelled by Referee decision. Runtime fallback to another provider or mock
provider is prohibited.

## Goal

Do not implement fallback routing. Retry the selected provider only, then return
its classified error.

## Scope

- In:
  - Marking the withdrawn fallback proposal and dependent issues as `wont_do`.
  - Keeping explicit no-fallback regression coverage in the Sakana/Ollama
    interoperability feature.
- Out:
  - Automatic model discovery or pricing feeds.
  - Dynamic fallback reordering.
  - Changes to model-name routing when no profile is present.

## Issue Graph

| Issue | Status | Depends on | Blocks | Branch |
| --- | --- | --- | --- | --- |
| LISS-0016 | wont_do | - | - | - |
| LISS-0018 | wont_do | - | - | - |
| LISS-0019 | wont_do | - | - | - |

## Recommended Order

1. Retain this document as the withdrawn proposal record.
2. Enforce no runtime fallback in provider interoperability tests and adapters.

## Current Next Issue

- No next issue; the work plan is cancelled.

## Risks

- Retry policy must remain bounded and provider-local.

## Verification Plan

- No implementation verification is applicable to this cancelled plan.
