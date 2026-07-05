# Template Rollout Specification

This specification covers this repository as a reusable AI-human collaboration
template. It must not define the product architecture, domain model, datastore,
external APIs, or feature specifications of a target repository.

## Scope

- Remove source-project residue from this template.
- Provide a repeatable way to copy the collaboration scaffolding into another
  repository.
- Provide a repeatable way to prepare the initial LLM session context after the
  template has been copied.
- Provide target-local onboarding guidance that does not overwrite the target
  repository README.
- Support lightweight operating paths that reduce unnecessary reasoning for
  mechanical work.
- Keep target-project architecture and specifications as placeholders or
  target-owned files.

## Out of Scope

- Choosing a target project stack.
- Creating target project domain specifications.
- Creating target project application code.
- Selecting concrete LLM providers, model names, databases, or third-party
  services for a target project.

## Scenarios

### Scenario: Source-project residue is absent

Given this repository is used as a generic collaboration template
When a maintainer searches the repository for the source project name
Then no reusable instruction, README, or specification text should refer to the
source project as part of the template identity.

### Scenario: Copy files into a new repository

Given a target repository path exists
And the target repository has no conflicting collaboration files
When the maintainer runs the copy script with the target path
Then the agent contract files, collaboration documents, architecture process
documents, templates, GitHub instruction files, issue placeholders, and
evaluation placeholders are copied into the target repository.

### Scenario: Copy files into an existing repository without changing its design

Given a target repository path exists
And it may already contain application README, architecture documents, or
feature specifications
When the maintainer runs the copy script without the force option
Then existing target files are left unchanged
And missing collaboration template files are added
And no target domain, datastore, provider, or stack decision is introduced.

### Scenario: Prepare an initial LLM setup prompt

Given the collaboration template files exist in a target repository
When the maintainer runs the LLM setup script
Then the script prints a compact prompt that instructs an AI agent to read the
required operating documents, select the smallest safe operating path, respect
phase gates, and ask for the target specification and requested phase before
implementation.

### Scenario: Guide midway adoption without changing target documentation

Given the target repository already has a product README
When the maintainer copies the collaboration template without the force option
Then the product README is left unchanged
And target-local collaboration onboarding remains available under
`docs/collaboration/`.

### Scenario: Fill generic placeholders only when explicitly supplied

Given the maintainer provides project name, domain summary, or stack text to
the copy script
When template files are copied
Then only generic placeholders for those fields are replaced
And unspecified architectural choices remain placeholders for the target
project to decide.
