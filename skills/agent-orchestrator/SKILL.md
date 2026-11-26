---
name: agent-orchestrator
description: Pick the model for a job and hand the work to it. Covers Claude and Codex subagents, the local models on this PC, and OpenRouter for images and for writing in a voice. Use when work is worth splitting across agents, when choosing a model for a subagent, when an image has to be generated, or when a social media post or a character's lines have to be written.
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
| Neon | Google | – | – | On trial: reviews, when Nicolas names it |

For grunt work, use Haiku or Luna. Do not use Astra or Sonnet: Nicolas does not trust Astra's work at the moment, and Sonnet costs too much for what it can do.

Take the newest version of a model, and look its ID up instead of writing one from memory. Match the effort to the task. Run a review with the `council-loop` skill.

## Reaching a model

- **Your own provider:** your native subagent tool.
- **The other provider, or when the effort level matters:** `delegate_task` in T3 Code.
- **Neon:** Google's `agy` command (below).

The other agent does not see this conversation. Write a brief with the goal, the files it owns, the constraints, and what done means. Check the diff and run the tests yourself before you accept its work.

In T3 Code:

- There is no read-only switch. For a review or a plan, write "Do not edit files" in the brief and check `git status` afterwards.
- `isolation: "worktree"` starts from the last commit, so commit first.
- Leave `serviceTier` at its default unless Nicolas asks for speed.
- The result names the provider, model and options that really ran. Check them.

### Neon

Neon runs through Google's command-line tool `agy`, on Nicolas's Google AI Pro plan. The plan's allowance is small, so spend it on the job at hand.

```sh
agy -p "$(cat brief.md)" --model gemini-4-neon-high --mode plan \
  --add-dir "$BRIEF_DIR" --output-format json --print-timeout 15m
```

- Run it from the repo's folder. The answer is the `response` field of the JSON.
- `agy models` lists the model IDs. The effort is the end of the ID: `-low`, `-medium`, `-high` or `-xhigh`.
- A run started this way cannot ask for permission. When Neon tries a shell command, the run ends with no answer. So for a review, write the diff to a file outside the repo (`git diff <base> > "$BRIEF_DIR/review.diff"`), pass that folder with `--add-dir`, and say in the brief to read files with its file tools and to run no commands.
- `--mode plan` is for a review or a plan. Still write "Do not edit files" in the brief and check `git status` afterwards.
- If it answers that it needs authentication, Nicolas has to sign in again: he runs `agy` once.

## Local models

Nicolas's PC serves open models through one gateway, [local_llm](https://github.com/NicolasMahn/local_llm). They cost only electricity and nothing goes to a third party. They are far weaker than the models above. Never give them coding or judgment work.

Use them for many small independent items (summaries, extraction, classification), for data that should stay private, and for speech, pictures and video. Send the requests in parallel: one at a time wastes most of the machine.

The gateway's address and key are in `~/.config/local-llm/account.env`: `LOCAL_LLM_URL` and `LOCAL_LLM_ADMIN_KEY`. Load the file in the command that needs them, and never write the values into a file tracked by git. The API is OpenAI-compatible at `$LOCAL_LLM_URL/v1` (Anthropic clients: `$LOCAL_LLM_URL`).

Many models are installed and only a few run at a time. The README of local_llm says what each is good at. The same key lists, starts and stops them:

```sh
. ~/.config/local-llm/account.env
curl -H "x-api-key: $LOCAL_LLM_ADMIN_KEY" "$LOCAL_LLM_URL/admin/models"
curl -X POST -H "x-api-key: $LOCAL_LLM_ADMIN_KEY" "$LOCAL_LLM_URL/admin/models/NAME/start"
curl -X POST -H "x-api-key: $LOCAL_LLM_ADMIN_KEY" "$LOCAL_LLM_URL/admin/models/NAME/stop"
```

A start answers `202` at once and then takes minutes. The list shows when the model is `live`, or in `failed_job` why it did not start. When it does not fit in memory, use a model that is already running. Stop only a model you started: Nicolas may be using the others.

Called through the API, a model sees only what is in the request. To let one read files and use tools, run it through Pi: in T3 Code, `delegate_task` with the provider `pi`. Pi may need to be configured on the fly, because it offers only the local models listed in `~/.pi/agent/models.json`. Add the one you need there. T3 Code picks the change up within about five minutes.

## OpenRouter

OpenRouter costs real money. Use it for images and for writing in a voice (below). Use it for other text only when the other provider cannot be reached and an outside view is the point of the task. Spend without asking, in proportion to the task and the balance.

Run `python3 scripts/openrouter.py status` first. It prints the balance, the current model IDs with prices, and the commands for an image or a consultation. It needs `OPENROUTER_API_KEY` in the environment. If the key is missing, say so and go on without OpenRouter.

For images, draft with the newest Gemini Flash image model, then render the chosen direction once with the newest GPT image model. Look at the result before you use it.

### Writing in a voice

Kimi K2 writes any text that has to sound like a person or a character: a social media post, or the lines a character speaks. The models in the table write clearly, and that is the problem here: their posts read like a fact sheet or like an ad.

A capable frontier agent (Fable or Opus) steers Kimi and does not write the text itself:

- **Brief it.** Say who is speaking and how they talk, give the true facts it may use, show what was rejected before and why, and ask for three different takes. Add a text Nicolas already accepted as the example of the voice.
- **Check every line for truth.** Kimi writes claims that sound right and are not.
- **Show the takes as Kimi wrote them.** Name what is false or missing next to them. Change only what is false, and do not smooth the rest into your own voice.

Reach it with `delegate_task`, provider `pi`, and tell it to write only: no commands, no files. Use `openrouter/moonshotai/kimi-k2-0905`, and stay on K2 until Nicolas asks for another Kimi.

## Handoff

Say which agents, local models and OpenRouter calls you used, and what they cost.
