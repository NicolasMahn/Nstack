---
name: agent-orchestrator
description: Pick the model for a job and hand the work to it. Covers Claude and Codex subagents, the local models on this PC, and OpenRouter for images. Use when work is worth splitting across agents, when choosing a model for a subagent, or when an image has to be generated.
---

# Agent orchestrator

Split work only when the parts are truly independent. Give each agent one clear task and the files it owns. You keep the final decision, the integration, and the check that it works. Do not delegate an explanation or a small change.

For a code change, work in stages: tests for the behavior that matters, then the change that makes them pass, then the docs and comments it made wrong. For work across components, agree on the interface first and give each component or shared file one owner. Before calling it done, check the seams: data shape, error handling, lifecycle, compatibility.

## Models

The scores are Nicolas's rough routing signals. Clarity means how easy the model's work is to follow: simple code and plain explanations.

| Model | Provider | Intelligence | Clarity | Use it for |
|---|---|---:|---:|---|
| Fable | Claude | 9.5 | 9 | Decisions where the answer is unclear |
| Opus | Claude | 9 | 8.5 | All code generation |
| Sol | Codex | 8.5 | 5 | Reviews |

For grunt work, use Haiku or Luna. Do not use Astra or Sonnet: Nicolas does not trust Astra's work at the moment, and Sonnet costs too much for what it can do.

Take the newest version of a model, and look its ID up instead of writing one from memory. Match the effort to the task. Run a review with the `council-loop` skill.

## Reaching a model

- **Your own provider:** your native subagent tool.
- **The other provider, or when the effort level matters:** `delegate_task` in T3 Code.
- **Codex from Claude Code outside T3 Code:** the `codex-threads` skill.

The other agent does not see this conversation. Write a brief with the goal, the files it owns, the constraints, and what done means. Check the diff and run the tests yourself before you accept its work.

In T3 Code:

- There is no read-only switch. For a review or a plan, write "Do not edit files" in the brief and check `git status` afterwards.
- `isolation: "worktree"` starts from the last commit, so commit first.
- Leave `serviceTier` at its default unless Nicolas asks for speed.
- The result names the provider, model and options that really ran. Check them.

## Local models

This PC serves open models through one gateway, [local_llm](https://github.com/NicolasMahn/local_llm), in `~/Projects/local_llm`. They cost only electricity and nothing leaves the machine. They are far weaker than the models above. Never give them coding or judgment work.

Use them for many small independent items (summaries, extraction, classification), for data that should stay private, and for speech, pictures and video. Send the requests in parallel: one at a time wastes most of the machine.

`~/Projects/local_llm/llm status` shows what is running, and the table at the top of the project's README says what each model is good at. The API is OpenAI-compatible at `http://localhost:8400/v1` (Anthropic clients: `http://localhost:8400`), with the key from `~/Projects/local_llm/llm key`. `llm up NAME` starts a model. Do not stop one you did not start: Nicolas may be using it.

Called through the API, a model sees only what is in the request. To let one read files and use tools, run it through Pi (`pi -p`). Pi may first need the gateway added as a provider in `~/.pi/agent/models.json`.

## OpenRouter

OpenRouter costs real money. Use it for images, and for text only when the other provider cannot be reached and an outside view is the point of the task. Spend without asking, in proportion to the task and the balance.

Run `python3 scripts/openrouter.py status` first. It prints the balance, the current model IDs with prices, and the commands for an image or a consultation. It needs `OPENROUTER_API_KEY` in the environment. If the key is missing, say so and go on without OpenRouter.

For images, draft with the newest Gemini Flash image model, then render the chosen direction once with the newest GPT image model. Look at the result before you use it.

## Handoff

Say which agents, local models and OpenRouter calls you used, and what they cost.
